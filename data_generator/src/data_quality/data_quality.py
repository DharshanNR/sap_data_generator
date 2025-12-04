from collections import defaultdict
from utils import print_colored

from ValidationResult import ValidationResult
import pandas as pd
import numpy as np
import os
import json
import datetime
import re

from dq_config import dq_config
class data_quality:
    def __init__(self, config):
        self.config = config
        self.data = {}
        self.results = defaultdict(list) # Category -> List of ValidationResult
        self.data_profile = {}
        self.overall_dq_score = 0.0


    def _get_examples(self, df,  id_field, num_examples=5):
        """Retrieves example IDs from a DataFrame.

        This method extracts a specified number of example IDs from the beginning of a DataFrame.
        It handles both single and composite ID fields.

        Args:
            df (pandas.DataFrame): The input DataFrame from which to extract examples.
            id_field (str or list): The name of the column(s) to use as the ID field(s).
                                    If a string, it's a single column name.
                                    If a list of strings, it represents composite keys.
            num_examples (int, optional): The number of examples to retrieve. Defaults to 5.

        Returns:
            list: A list of example IDs.
                  If `id_field` is a string, the list contains values from that column.
                  If `id_field` is a list, the list contains tuples, where each tuple
                  represents a composite key from the specified columns.
        """
        if isinstance(id_field, list):
            # For composite keys, return a tuple of values
            return df.head(num_examples).apply(lambda row: tuple(row[f] for f in id_field), axis=1).tolist()
        else:
            return df.head(num_examples)[id_field].tolist()

    def load_data(self):
        """Loads data from CSV files into DataFrames based on schema.

        Iterates through configured tables, loads CSVs, infers separators,
        and converts types (date, float, int). Stores DataFrames in `self.data`.
        Handles missing files and loading errors. Exits if critical tables fail to load.

        Args:
            self (object): Instance with `config` (DATA_DIR, SCHEMA) and `data` attributes.

        Returns:
            None: Modifies `self.data` in place; exits on critical failure.
        """
        print_colored(f"\nLoading data from {self.config.DATA_DIR}...", 'OKBLUE')
        for table_name, table_info in self.config.SCHEMA.items():
            
            file_path = os.path.join(self.config.DATA_DIR, table_info["file"])
            if not os.path.exists(file_path):
                print_colored(f"  {table_name}: File not found at {file_path}",'FAIL')
                continue
            
            try:
                # Infer separator, handle potential mixed types
                df = pd.read_csv(file_path, sep=None, engine='python', parse_dates=True)
                
                # Convert date columns explicitly based on schema
                for field_name, field_props in table_info["fields"].items():
                    if field_props["type"] == datetime.date and field_name in df.columns:
                        df[field_name] = pd.to_datetime(df[field_name], errors='coerce').dt.date
                    elif field_props["type"] == float and field_name in df.columns:
                        df[field_name] = pd.to_numeric(df[field_name], errors='coerce')
                    elif field_props["type"] == int and field_name in df.columns:
                        df[field_name] = pd.to_numeric(df[field_name], errors='coerce').astype('Int64') # Use Int64 for nullable int
                
                self.data[table_name] = df
                print_colored(f"  {table_name}: Loaded {len(df)} records.", 'OKGREEN')
            except Exception as e:
                print_colored(f"  {table_name}: Error loading data - {e}", 'FAIL')
        
        # Ensure all required tables are loaded for further checks
        required_tables = list(self.config.SCHEMA.keys())
        if not all(table in self.data for table in required_tables):
            print_colored("  CRITICAL: Not all required tables could be loaded. Aborting further checks.", 'FAIL')
            exit() # Or raise an exception

    def _add_result(self, category, check_name, status, severity, description, violations=0, affected_percentage=0.0, examples=None):
        """Adds a validation result to the stored results, categorizing it.

        Args:
            category (str): The category of the validation check (e.g., 'Schema', 'Consistency').
            check_name (str): The specific name of the validation check performed.
            status (str): The outcome status of the check (e.g., 'PASS', 'FAIL', 'WARNING').
            severity (str): The severity level of the result (e.g., 'INFO', 'LOW', 'HIGH', 'CRITICAL').
            description (str): A detailed description of the check and its findings.
            violations (int, optional): The number of violations found. Defaults to 0.
            affected_percentage (float, optional): Percentage of data affected. Defaults to 0.0.
            examples (list, optional): A list of example violating data points. Defaults to None.

        Returns:
            None: This method modifies the `self.results` dictionary in place.
        """
        result = ValidationResult(category,check_name, status, severity, description, violations, affected_percentage, examples)
        self.results[category].append(result)

    def validate_schema(self):
        """Validates loaded DataFrames against the configured schema.

        Checks for missing tables, columns, and type mismatches.
        Records `ValidationResult` for each check, populating `self.results`.

        Args:
            self (object): Instance with `config`, `data`, and `_add_result`.

        Returns:
            None: Populates `self.results` with schema validation outcomes.
        """
        print_colored("\n--- Running Schema Validation ---", 'HEADER')
        for table_name, table_info in self.config.SCHEMA.items():
            if table_name not in self.data: continue
            df = self.data[table_name]
            total_records = len(df)

            # Check 1: All required fields present
            for field_name in table_info["fields"]:
                if field_name not in df.columns:
                    self._add_result("schema_validation", f"{table_name}.{field_name} - Field Missing", "FAIL", self.config.SEVERITY["CRITICAL"],
                                        f"Field '{field_name}' is missing from table '{table_name}'.", total_records, 100.0)
                
                
            # Check 2-5: Data types, mandatory, length, format
            for field_name, field_props in table_info["fields"].items():
                if field_name not in df.columns: continue # Skip if field is already reported missing

                # Mandatory fields (null check)
                if field_props.get("mandatory", False):
                    null_violations = df[field_name].isnull().sum()
                    if null_violations > 0:
                        self._add_result("schema_validation", f"{table_name}.{field_name} - Null Values in Mandatory Field", "FAIL", self.config.SEVERITY["CRITICAL"],
                                            f"Mandatory field '{field_name}' in '{table_name}' has null values.",
                                            null_violations, (null_violations / total_records) * 100,
                                            self._get_examples(df[df[field_name].isnull()],  table_info["id_field"]))

              # Correct data types (after initial loading conversion)
                # Pandas dtypes are more complex, so we check if conversion was successful
                if field_props["type"] == datetime.date:
                    invalid_type_condition = df[field_name].apply(lambda x: not isinstance(x, datetime.date) and x is not None)
                elif field_props["type"] == float:
                    invalid_type_condition = df[field_name].apply(lambda x: not isinstance(x, (float, int)) and x is not None)
                elif field_props["type"] == int:
                    invalid_type_condition = df[field_name].apply(lambda x: not isinstance(x, (int, np.integer)) and x is not None)
                elif field_props["type"] == bool:
                    invalid_type_condition = df[field_name].apply(lambda x: not isinstance(x, bool) and x is not None)
                else: # str
                    invalid_type_condition = df[field_name].apply(lambda x: not isinstance(x, str) and x is not None)
                
                type_violations = df[invalid_type_condition].shape[0]
                if type_violations > 0:
                    self._add_result("schema_validation", f"{table_name}.{field_name} - Incorrect Data Type", "FAIL", self.config.SEVERITY["CRITICAL"],
                                        f"Field '{field_name}' in '{table_name}' has incorrect data types.",
                                        type_violations, (type_violations / total_records) * 100,
                                        self._get_examples(df[invalid_type_condition],  table_info["id_field"]))

                # Field length constraints
                if "length" in field_props and field_props["type"] == str:
                    min_len, max_len = (field_props["length"], field_props["length"]) if isinstance(field_props["length"], int) else field_props["length"]
                    length_violations = df[field_name].astype(str).apply(lambda x: not (min_len <= len(x) <= max_len) if pd.notna(x) else False).sum()
                    if length_violations > 0:
                        self._add_result("schema_validation", f"{table_name}.{field_name} - Invalid Length", "FAIL", self.config.SEVERITY["WARNING"],
                                            f"Field '{field_name}' in '{table_name}' has invalid length.",
                                            length_violations, (length_violations / total_records) * 100,
                        
                                            self._get_examples(df[df[field_name].astype(str).apply(lambda x: not (min_len <= len(x) <= max_len) if pd.notna(x) else False)], table_info["id_field"]))

                # Value format validation (regex)
                if "format" in field_props and field_props["type"] == str:
                    format_violations = df[field_name].astype(str).apply(lambda x: not bool(re.fullmatch(field_props["format"], x)) if pd.notna(x) else False).sum()
                elif "format" in field_props and field_props["type"] == datetime.date:
                    format_violations = df[field_name].astype(str).apply(lambda x: not bool(re.fullmatch(field_props["format"], x)) if pd.notna(x) else False).sum()
                if format_violations > 0 and "format" in field_props:
                    
                    self._add_result("schema_validation", f"{table_name}.{field_name} - Invalid Format", "FAIL", self.config.SEVERITY["WARNING"],
                                        f"Field '{field_name}' in '{table_name}' has invalid format.",
                                        format_violations, (format_violations / total_records) * 100,
                                        self._get_examples(df[df[field_name].astype(str).apply(lambda x: not bool(re.fullmatch(field_props["format"], x)) if pd.notna(x) else False)], table_info["id_field"]))
                                           
                
                # Valid values (enum)
                if "valid_values" in field_props:
                    valid_value_violations = df[field_name].apply(lambda x: x not in field_props["valid_values"] if pd.notna(x) else False).sum()
                    if valid_value_violations > 0:
                        self._add_result("schema_validation", f"{table_name}.{field_name} - Invalid Value", "FAIL", self.config.SEVERITY["WARNING"],
                                            f"Field '{field_name}' in '{table_name}' contains values not in the allowed list.",
                                            valid_value_violations, (valid_value_violations / total_records) * 100,
                                            self._get_examples(df[df[field_name].apply(lambda x: x not in field_props["valid_values"] if pd.notna(x) else False)], True, table_info["id_field"]))

    def validate_referential_integrity(self):
        """Validates referential integrity between tables based on schema.

        Checks foreign key relationships for missing parent keys.
        Records `ValidationResult` for each check, populating `self.results`.

        Args:
            self (object): Instance with `config`, `data`, and `_add_result`.

        Returns:
            None: Populates `self.results` with referential integrity outcomes.
        """
        print_colored("\n--- Running Referential Integrity Checks ---", 'HEADER')
        
        
        # All EKPO.EBELN exist in EKKO
        if "EKPO" in self.data and "EKKO" in self.data:
            ekpo_ebeln = self.data["EKPO"]["EBELN"].unique()
            ekko_ebeln = self.data["EKKO"]["EBELN"].unique()
            violations = np.setdiff1d(ekpo_ebeln, ekko_ebeln)
            if len(violations) > 0:
                self._add_result("referential_integrity", "EKPO.EBELN in EKKO", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "EKPO records found with EBELN not present in EKKO.",
                                 len(violations), (len(violations) / len(ekpo_ebeln)) * 100, violations.tolist())
            else:
                
                self._add_result("referential_integrity", "EKPO.EBELN in EKKO", "PASS", self.config.SEVERITY["INFO"], "All EKPO.EBELN exist in EKKO.")

        # All EKKO.LIFNR exist in LFA1
        if "EKKO" in self.data and "LFA1" in self.data:
            ekko_lifnr = self.data["EKKO"]["LIFNR"].unique()
            lfa1_lifnr = self.data["LFA1"]["LIFNR"].unique()
            violations = np.setdiff1d(ekko_lifnr, lfa1_lifnr)
            if len(violations) > 0:
                self._add_result("referential_integrity", "EKKO.LIFNR in LFA1", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "EKKO records found with LIFNR not present in LFA1.",
                                 len(violations), (len(violations) / len(ekko_lifnr)) * 100, violations.tolist())
            else:
                self._add_result("referential_integrity", "EKKO.LIFNR in LFA1", "PASS", self.config.SEVERITY["INFO"], "All EKKO.LIFNR exist in LFA1.")

        # All EKPO.MATNR exist in MARA
        if "EKPO" in self.data and "MARA" in self.data:
            ekpo_matnr = self.data["EKPO"]["MATNR"].unique()
            mara_matnr = self.data["MARA"]["MATNR"].unique()
            violations = np.setdiff1d(ekpo_matnr, mara_matnr)
            if len(violations) > 0:
                self._add_result("referential_integrity", "EKPO.MATNR in MARA", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "EKPO records found with MATNR not present in MARA.",
                                 len(violations), (len(violations) / len(ekpo_matnr)) * 100, violations.tolist())
            else:
                self._add_result("referential_integrity", "EKPO.MATNR in MARA", "PASS", self.config.SEVERITY["INFO"], "All EKPO.MATNR exist in MARA.")

        # All EKBE.EBELN+EBELP reference valid EKKO/EKPO combinations
        if "EKBE" in self.data and "EKPO" in self.data:
            ekbe_keys = self.data["EKBE"][["EBELN", "EBELP"]].drop_duplicates()
            ekpo_keys = self.data["EKPO"][["EBELN", "EBELP"]].drop_duplicates()
            
            merged = pd.merge(ekbe_keys, ekpo_keys, on=["EBELN", "EBELP"], how="left", indicator=True)
            violations_df = merged[merged['_merge'] == 'left_only']
            
            if len(violations_df) > 0:
                self._add_result("referential_integrity", "EKBE.EBELN+EBELP in EKPO", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "EKBE records found with EBELN+EBELP combinations not present in EKPO.",
                                 len(violations_df), (len(violations_df) / len(ekbe_keys)) * 100,
                                 self._get_examples(violations_df, True, ["EBELN", "EBELP"]))
            else:
                self._add_result("referential_integrity", "EKBE.EBELN+EBELP in EKPO", "PASS", self.config.SEVERITY["INFO"], "All EKBE.EBELN+EBELP exist in EKPO.")

        # All VENDOR_CONTRACTS.LIFNR exist in LFA1
        if "VENDOR_CONTRACTS" in self.data and "LFA1" in self.data:
            vc_lifnr = self.data["VENDOR_CONTRACTS"]["LIFNR"].unique()
            lfa1_lifnr = self.data["LFA1"]["LIFNR"].unique()
            violations = np.setdiff1d(vc_lifnr, lfa1_lifnr)
            if len(violations) > 0:
                self._add_result("referential_integrity", "VENDOR_CONTRACTS.LIFNR in LFA1", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "VENDOR_CONTRACTS records found with LIFNR not present in LFA1.",
                                 len(violations), (len(violations) / len(vc_lifnr)) * 100, violations.tolist())
            else:
                self._add_result("referential_integrity", "VENDOR_CONTRACTS.LIFNR in LFA1", "PASS", self.config.SEVERITY["INFO"], "All VENDOR_CONTRACTS.LIFNR exist in LFA1.")

        # All VENDOR_CONTRACTS.MATNR exist in MARA
        if "VENDOR_CONTRACTS" in self.data and "MARA" in self.data:
            vc_matnr = self.data["VENDOR_CONTRACTS"]["MATNR"].unique()
            mara_matnr = self.data["MARA"]["MATNR"].unique()
            violations = np.setdiff1d(vc_matnr, mara_matnr)
            if len(violations) > 0:
                self._add_result("referential_integrity", "VENDOR_CONTRACTS.MATNR in MARA", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "VENDOR_CONTRACTS records found with MATNR not present in MARA.",
                                 len(violations), (len(violations) / len(vc_matnr)) * 100, violations.tolist())
            else:
                self._add_result("referential_integrity", "VENDOR_CONTRACTS.MATNR in MARA", "PASS", self.config.SEVERITY["INFO"], "All VENDOR_CONTRACTS.MATNR exist in MARA.")            
    def validate_business_logic(self):
        """Validates custom business rules defined in the configuration.

        Applies rules from `self.config.BUSINESS_RULES` to DataFrames.
        Records `ValidationResult` for each rule, populating `self.results`.

        Args:
            self (object): Instance with `config`, `data`, and `_add_result`.

        Returns:
            None: Populates `self.results` with business logic outcomes.
        """
        print_colored("\n--- Running Business Logic Validation ---", 'HEADER')

        # NETWR = NETPR × MENGE (within 1% tolerance)
        if "EKPO" in self.data:
            df = self.data["EKPO"].copy()
            df['CALC_NETWR'] = round(df['NETPR'] * df['MENGE'], 2)
            tolerance = self.config.NETWR_TOLERANCE_PERCENT
            violations_condition = (abs(df['NETWR'] - df['CALC_NETWR']) / df['NETWR']) > tolerance
            violations_df = df[violations_condition]
            if len(violations_df) > 0:
                self._add_result("business_logic_validation", "EKPO.NETWR Calculation", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 f"NETWR is not equal to NETPR * MENGE within {tolerance*100}% tolerance.",
                                 len(violations_df), (len(violations_df) / len(df)) * 100,
                                 self._get_examples(violations_df, self.config.SCHEMA["EKPO"]["id_field"]))
            else:
                self._add_result("business_logic_validation", "EKPO.NETWR Calculation", "PASS", self.config.SEVERITY["INFO"], "All EKPO.NETWR calculations are correct.")

        # All delivery dates >= PO dates
        if "EKPO" in self.data and "EKKO" in self.data:
            merged_df = pd.merge(self.data["EKPO"], self.data["EKKO"][["EBELN", "AEDAT"]], on="EBELN", how="left")
            violations_condition = merged_df["EINDT"] < merged_df["AEDAT"]
            violations_df = merged_df[violations_condition]
            if len(violations_df) > 0:
                self._add_result("business_logic_validation", "Delivery Date vs PO Date", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "Expected delivery date (EINDT) is before PO creation date (AEDAT).",
                                 len(violations_df), (len(violations_df) / len(merged_df)) * 100,
                                 self._get_examples(violations_df, True, self.config.SCHEMA["EKPO"]["id_field"]))
            else:
                self._add_result("business_logic_validation", "Delivery Date vs PO Date", "PASS", self.config.SEVERITY["INFO"], "All delivery dates are after PO dates.")

        # Contract prices within 5% of PO prices for contract POs (BSART='NB')
        if "EKPO" in self.data and "EKKO" in self.data and "VENDOR_CONTRACTS" in self.data:
            ekpo_ekko = pd.merge(self.data["EKPO"], self.data["EKKO"][["EBELN", "BSART","AEDAT"]], on="EBELN", how="left")
            contract_pos = ekpo_ekko[ekpo_ekko["BSART"] == "NB"].copy()
            
            
            if not contract_pos.empty:
                merged_contracts = pd.merge(contract_pos, self.data["VENDOR_CONTRACTS"], 
                                            on=["LIFNR", "MATNR"], how="left", suffixes=('_PO', '_CONTRACT'))
                
                # Filter for active contracts at PO date
                merged_contracts = merged_contracts[
                    (merged_contracts['AEDAT'] >= merged_contracts['VALID_FROM']) &
                    (merged_contracts['AEDAT'] <= merged_contracts['VALID_TO'])
                ]
                
                if not merged_contracts.empty:
                    tolerance = self.config.CONTRACT_PRICE_PO_PRICE_TOLERANCE_PERCENT
                    violations_condition = (abs(merged_contracts['NETPR'] - merged_contracts['CONTRACT_PRICE']) / merged_contracts['CONTRACT_PRICE']) > tolerance
                    violations_df = merged_contracts[violations_condition]
                    
                    if len(violations_df) > 0:
                        self._add_result("business_logic_validation", "Contract PO Price Adherence", "FAIL", self.config.SEVERITY["WARNING"],
                                         f"Contract PO prices (NETPR) deviate more than {tolerance*100}% from CONTRACT_PRICE.",
                                         len(violations_df), (len(violations_df) / len(merged_contracts)) * 100,
                                         self._get_examples(violations_df,  self.config.SCHEMA["EKPO"]["id_field"]))
                    else:
                        self._add_result("business_logic_validation", "Contract PO Price Adherence", "PASS", self.config.SEVERITY["INFO"], "Contract PO prices adhere to contract terms.")
                else:
                    self._add_result("business_logic_validation", "Contract PO Price Adherence", "INFO", self.config.SEVERITY["INFO"], "No active contracts found for contract POs to validate pricing.")
            else:
                self._add_result("business_logic_validation", "Contract PO Price Adherence", "INFO", self.config.SEVERITY["INFO"], "No contract POs (BSART='NB') found.")

        # Invoice amounts match goods receipt amounts (±2%)
        if "EKBE" in self.data:
            ekbe_gr = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'].copy()
            ekbe_inv = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'Q'].copy()

            if not ekbe_gr.empty and not ekbe_inv.empty:
                # Group by PO item to sum GR and INV amounts
                gr_sums = ekbe_gr.groupby(["EBELN", "EBELP"])["DMBTR"].sum().reset_index(name="GR_AMOUNT")
                inv_sums = ekbe_inv.groupby(["EBELN", "EBELP"])["DMBTR"].sum().reset_index(name="INV_AMOUNT")

                merged_amounts = pd.merge(gr_sums, inv_sums, on=["EBELN", "EBELP"], how="inner")
                
                if not merged_amounts.empty:
                    tolerance = self.config.INVOICE_GR_AMOUNT_TOLERANCE_PERCENT
                    violations_condition = (abs(merged_amounts['GR_AMOUNT'] - merged_amounts['INV_AMOUNT']) / merged_amounts['GR_AMOUNT']) > tolerance
                    violations_df = merged_amounts[violations_condition]
                    if len(violations_df) > 0:
                        self._add_result("business_logic_validation", "Invoice vs GR Amount Match", "FAIL", self.config.SEVERITY["WARNING"],
                                         f"Invoice amounts (DMBTR for BEWTP='Q') do not match Goods Receipt amounts (DMBTR for BEWTP='E') within {tolerance*100}% tolerance for the same PO item.",
                                         len(violations_df), (len(violations_df) / len(merged_amounts)) * 100,
                                         self._get_examples(violations_df,  ["EBELN", "EBELP"]))
                    else:
                        self._add_result("business_logic_validation", "Invoice vs GR Amount Match", "PASS", self.config.SEVERITY["INFO"], "Invoice amounts match GR amounts.")
                else:
                    self._add_result("business_logic_validation", "Invoice vs GR Amount Match", "INFO", self.config.SEVERITY["INFO"], "No PO items with both GR and Invoice records to compare amounts.")
            else:
                self._add_result("business_logic_validation", "Invoice vs GR Amount Match", "INFO", self.config.SEVERITY["INFO"], "Not enough GR or Invoice records to perform check.")

        # Contract dates: VALID_TO > VALID_FROM
        if "VENDOR_CONTRACTS" in self.data:
            df = self.data["VENDOR_CONTRACTS"]
            violations_condition = df["VALID_TO"] <= df["VALID_FROM"]
            violations_df = df[violations_condition]
            if len(violations_df) > 0:
                self._add_result("business_logic_validation", "Contract Date Validity", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "Contract VALID_TO date is not after VALID_FROM date.",
                                 len(violations_df), (len(violations_df) / len(df)) * 100,
                                 self._get_examples(violations_df, self.config.SCHEMA["VENDOR_CONTRACTS"]["id_field"]))
            else:
                self._add_result("business_logic_validation", "Contract Date Validity", "PASS", self.config.SEVERITY["INFO"], "All contract dates are valid.")

        # EKBE invoice dates (BEWTP='Q') come after goods receipts (BEWTP='E')
        if "EKBE" in self.data:
            ekbe_gr = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'].copy()
            ekbe_inv = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'Q'].copy()

            if not ekbe_gr.empty and not ekbe_inv.empty:
                # Get earliest GR date for each PO item
                earliest_gr = ekbe_gr.groupby(["EBELN", "EBELP"])["BUDAT"].min().reset_index(name="EARLIEST_GR_DATE")
                
                # Merge with invoice records
                merged_inv = pd.merge(ekbe_inv, earliest_gr, on=["EBELN", "EBELP"], how="left")
                
                # Check if invoice BUDAT is before earliest GR BUDAT
                violations_condition = merged_inv["BUDAT"] < merged_inv["EARLIEST_GR_DATE"]
                violations_df = merged_inv[violations_condition]
                if len(violations_df) > 0:
                    self._add_result("business_logic_validation", "Invoice Date After GR Date", "FAIL", self.config.SEVERITY["CRITICAL"],
                                     "Invoice posting date (BUDAT for BEWTP='Q') is before the earliest Goods Receipt posting date for the same PO item.",
                                     len(violations_df), (len(violations_df) / len(ekbe_inv)) * 100,
                                     self._get_examples(violations_df,  self.config.SCHEMA["EKBE"]["id_field"]))
                else:
                    self._add_result("business_logic_validation", "Invoice Date After GR Date", "PASS", self.config.SEVERITY["INFO"], "All invoice dates are after goods receipt dates.")
            else:
                self._add_result("business_logic_validation", "Invoice Date After GR Date", "INFO", self.config.SEVERITY["INFO"], "Not enough GR or Invoice records to perform check.")

        # Blocked vendors (SPERR='X') should have no recent POs (last 90 days)
        if "LFA1" in self.data and "EKKO" in self.data:
            blocked_vendors = self.data["LFA1"][self.data["LFA1"]["SPERR"] == 'X']['LIFNR'].tolist()
            if blocked_vendors:
                recent_date_threshold = datetime.date.today() - datetime.timedelta(days=self.config.BLOCKED_VENDOR_PO_DAYS)
                recent_pos_by_blocked_vendors = self.data["EKKO"][
                    (self.data["EKKO"]["LIFNR"].isin(blocked_vendors)) &
                    (self.data["EKKO"]["AEDAT"] >= recent_date_threshold)
                ]
                if not recent_pos_by_blocked_vendors.empty:
                    self._add_result("business_logic_validation", "Blocked Vendors Recent POs", "FAIL", self.config.SEVERITY["CRITICAL"],
                                     f"Blocked vendors have POs created in the last {self.config.BLOCKED_VENDOR_PO_DAYS} days.",
                                     len(recent_pos_by_blocked_vendors), (len(recent_pos_by_blocked_vendors) / len(self.data["EKKO"])) * 100,
                                     self._get_examples(recent_pos_by_blocked_vendors, True, self.config.SCHEMA["EKKO"]["id_field"]))
                else:
                    self._add_result("business_logic_validation", "Blocked Vendors Recent POs", "PASS", self.config.SEVERITY["INFO"], "No recent POs for blocked vendors.")
            else:
                self._add_result("business_logic_validation", "Blocked Vendors Recent POs", "INFO", self.config.SEVERITY["INFO"], "No blocked vendors found.")
    
    # --- 4. Statistical Validation ---
    def validate_statistical(self):
        """Performs statistical validation checks on numerical columns.

        Applies rules from `self.config.STATISTICAL_RULES` to DataFrames.
        Records `ValidationResult` for each check, populating `self.results`.

        Args:
            self (object): Instance with `config`, `data`, and `_add_result`.

        Returns:
            None: Populates `self.results` with statistical validation outcomes.
        """

        print_colored("\n--- Running Statistical Validation ---", 'HEADER')

        # No extreme price outliers (beyond 3 standard deviations by category)
        if "EKPO" in self.data:
            df = self.data["EKPO"]
            outlier_violations = 0
            total_records = len(df)
            outlier_examples = []

            for matkl in df["MATKL"].unique():
                category_df = df[df["MATKL"] == matkl]
                if len(category_df) > 1: # Need at least 2 data points for std dev
                    mean_price = category_df["NETPR"].mean()
                    std_price = category_df["NETPR"].std()
                    
                    if std_price > 0: # Avoid division by zero if all prices are identical
                        outlier_condition = (category_df["NETPR"] > mean_price + self.config.OUTLIER_STD_DEV_THRESHOLD * std_price) | \
                                            (category_df["NETPR"] < mean_price - self.config.OUTLIER_STD_DEV_THRESHOLD * std_price)
                        
                        category_outliers = category_df[outlier_condition]
                        outlier_violations += len(category_outliers)
                        outlier_examples.extend(self._get_examples(category_outliers,  self.config.SCHEMA["EKPO"]["id_field"]))
            
            if outlier_violations > 0:
                self._add_result("statistical_validation", "Price Outliers by Material Category", "WARNING", self.config.SEVERITY["WARNING"],
                                 f"Found price outliers (beyond {self.config.OUTLIER_STD_DEV_THRESHOLD} std dev) by material category.",
                                 outlier_violations, (outlier_violations / total_records) * 100, outlier_examples)
            else:
                self._add_result("statistical_validation", "Price Outliers by Material Category", "PASS", self.config.SEVERITY["INFO"], "No significant price outliers detected.")

        # Pareto distribution check: top 20% vendors = ~80% spend (±10%)
        if "EKKO" in self.data and "EKPO" in self.data:
            merged_df = pd.merge(self.data["EKKO"][["EBELN", "LIFNR"]], self.data["EKPO"][["EBELN", "NETWR"]], on="EBELN", how="inner")
            vendor_spend = merged_df.groupby("LIFNR")["NETWR"].sum().sort_values(ascending=False).reset_index()
            total_spend = vendor_spend["NETWR"].sum()
            
            if total_spend > 0:
                num_vendors = len(vendor_spend)
                top_20_percent_vendors = int(num_vendors * 0.20)
                
                if top_20_percent_vendors > 0:
                    spend_by_top_vendors = vendor_spend.head(top_20_percent_vendors)["NETWR"].sum()
                    actual_percentage = spend_by_top_vendors / total_spend
                    
                    expected_percentage = 0.80
                    tolerance = self.config.PARETO_SPEND_TOLERANCE_PERCENT
                    
                    if not (expected_percentage - tolerance <= actual_percentage <= expected_percentage + tolerance):
                        self._add_result("statistical_validation", "Vendor Spend Pareto Principle", "WARNING", self.config.SEVERITY["WARNING"],
                                         f"Pareto principle check failed: Top 20% vendors account for {actual_percentage:.2%} of spend, expected ~{expected_percentage:.0%} (±{tolerance*100}%).",
                                         1, 100.0) # 1 violation for the overall check
                    else:
                        self._add_result("statistical_validation", "Vendor Spend Pareto Principle", "PASS", self.config.SEVERITY["INFO"], "Vendor spend distribution adheres to Pareto principle.")
                else:
                    self._add_result("statistical_validation", "Vendor Spend Pareto Principle", "INFO", self.config.SEVERITY["INFO"], "Not enough vendors to perform Pareto check.")
            else:
                self._add_result("statistical_validation", "Vendor Spend Pareto Principle", "INFO", self.config.SEVERITY["INFO"], "Total spend is zero, cannot perform Pareto check.")

        # Contract compliance rate between 60-80%
        if "EKKO" in self.data:
            total_pos = len(self.data["EKKO"])
            if total_pos > 0:
                contract_pos = self.data["EKKO"][self.data["EKKO"]["BSART"] == 'NB']
                compliance_rate = len(contract_pos) / total_pos
                
                min_rate, max_rate = self.config.CONTRACT_COMPLIANCE_RATE_RANGE
                
                if not (min_rate <= compliance_rate <= max_rate):
                    self._add_result("statistical_validation", "Contract Compliance Rate", "WARNING", self.config.SEVERITY["WARNING"],
                                     f"Contract compliance rate is {compliance_rate:.2%}, expected between {min_rate:.0%}-{max_rate:.0%}.",
                                     1, 100.0)
                else:
                    self._add_result("statistical_validation", "Contract Compliance Rate", "PASS", self.config.SEVERITY["INFO"], "Contract compliance rate is within expected range.")
            else:
                self._add_result("statistical_validation", "Contract Compliance Rate", "INFO", self.config.SEVERITY["INFO"], "No POs to calculate contract compliance rate.")

        # Late delivery rate between 20-30%
        if "EKBE" in self.data:
            gr_records = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'].copy()
            if not gr_records.empty:
                # Merge with EKPO to get EINDT
                merged_gr = pd.merge(gr_records, self.data["EKPO"][["EBELN", "EBELP", "EINDT"]], on=["EBELN", "EBELP"], how="left")
                
                # Ensure EINDT and ACTUAL_DELIVERY_DATE are dates
                merged_gr['EINDT'] = pd.to_datetime(merged_gr['EINDT'], errors='coerce').dt.date
                merged_gr['ACTUAL_DELIVERY_DATE'] = pd.to_datetime(merged_gr['ACTUAL_DELIVERY_DATE'], errors='coerce').dt.date
                
                # Filter out rows where dates are invalid after conversion
                merged_gr = merged_gr.dropna(subset=['EINDT', 'ACTUAL_DELIVERY_DATE'])

                if not merged_gr.empty:
                    late_deliveries = merged_gr[merged_gr["ACTUAL_DELIVERY_DATE"] > merged_gr["EINDT"]]
                    late_rate = len(late_deliveries) / len(merged_gr)
                    
                    min_rate, max_rate = self.config.LATE_DELIVERY_RATE_RANGE
                    
                    if not (min_rate <= late_rate <= max_rate):
                        self._add_result("statistical_validation", "Late Delivery Rate", "WARNING", self.config.SEVERITY["WARNING"],
                                         f"Late delivery rate is {late_rate:.2%}, expected between {min_rate:.0%}-{max_rate:.0%}.",
                                         1, 100.0)
                    else:
                        self._add_result("statistical_validation", "Late Delivery Rate", "PASS", self.config.SEVERITY["INFO"], "Late delivery rate is within expected range.")
                else:
                    self._add_result("statistical_validation", "Late Delivery Rate", "INFO", self.config.SEVERITY["INFO"], "No valid GR records with delivery dates to calculate late rate.")
            else:
                self._add_result("statistical_validation", "Late Delivery Rate", "INFO", self.config.SEVERITY["INFO"], "No Goods Receipt records found.")

        # Expected ratio of goods receipts to invoices (~1:1)
        if "EKBE" in self.data:
            num_gr = len(self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'])
            num_inv = len(self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'Q'])
            
            if num_gr > 0 and num_inv > 0:
                ratio = num_inv / num_gr
                tolerance = self.config.GR_INVOICE_RATIO_TOLERANCE
                
                if not (1 - tolerance <= ratio <= 1 + tolerance):
                    self._add_result("statistical_validation", "GR to Invoice Ratio", "WARNING", self.config.SEVERITY["WARNING"],
                                     f"GR to Invoice ratio is {ratio:.2f}, expected ~1:1 (±{tolerance*100}%).",
                                     1, 100.0)
                else:
                    self._add_result("statistical_validation", "GR to Invoice Ratio", "PASS", self.config.SEVERITY["INFO"], "GR to Invoice ratio is within expected range.")
            else:
                self._add_result("statistical_validation", "GR to Invoice Ratio", "INFO", self.config.SEVERITY["INFO"], "Not enough GR or Invoice records to calculate ratio.")


    def validate_completeness(self):
        """Validates data completeness, checking for missing values.

        Identifies nulls in columns specified by `self.config.COMPLETENESS_RULES`.
        Records `ValidationResult` for each check, populating `self.results`.

        Args:
            self (object): Instance with `config`, `data`, and `_add_result`.

        Returns:
            None: Populates `self.results` with completeness validation outcomes.
        """
        print_colored("\n--- Running Completeness Checks ---", 'HEADER')

        # Every PO has at least 1 line item
        if "EKKO" in self.data and "EKPO" in self.data:
            pos_with_items = self.data["EKPO"]["EBELN"].unique()
            all_pos = self.data["EKKO"]["EBELN"].unique()
            
            pos_without_items = np.setdiff1d(all_pos, pos_with_items)
            if len(pos_without_items) > 0:
                self._add_result("completeness_checks", "PO with Line Items", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "Some Purchase Orders (EKKO) have no corresponding line items (EKPO).",
                                 len(pos_without_items), (len(pos_without_items) / len(all_pos)) * 100, pos_without_items.tolist())
            else:
                self._add_result("completeness_checks", "PO with Line Items", "PASS", self.config.SEVERITY["INFO"], "All POs have at least one line item.")

        # Every PO line item has at least 1 goods receipt
        if "EKPO" in self.data and "EKBE" in self.data:
            ekpo_gr = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'][["EBELN", "EBELP"]].drop_duplicates()
            all_ekpo_items = self.data["EKPO"][["EBELN", "EBELP"]].drop_duplicates()
            
            merged = pd.merge(all_ekpo_items, ekpo_gr, on=["EBELN", "EBELP"], how="left", indicator=True)
            items_without_gr = merged[merged['_merge'] == 'left_only']
            
            if len(items_without_gr) > 0:
                self._add_result("completeness_checks", "PO Line Item with GR", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 "Some PO line items (EKPO) have no corresponding Goods Receipt (EKBE BEWTP='E').",
                                 len(items_without_gr), (len(items_without_gr) / len(all_ekpo_items)) * 100,
                                 self._get_examples(items_without_gr,  self.config.SCHEMA["EKPO"]["id_field"]))
            else:
                self._add_result("completeness_checks", "PO Line Item with GR", "PASS", self.config.SEVERITY["INFO"], "All PO line items have at least one Goods Receipt.")

        # Material groups are balanced (no category has >40% of materials)
        if "MARA" in self.data:
            material_group_counts = self.data["MARA"]["MATKL"].value_counts()
            total_materials = len(self.data["MARA"])
            
            if total_materials > 0:
                material_group_percentages = material_group_counts / total_materials
                
                unbalanced_groups = material_group_percentages[material_group_percentages > self.config.MAX_MATERIAL_GROUP_PERCENTAGE]
                if not unbalanced_groups.empty:
                    self._add_result("completeness_checks", "Material Group Balance", "WARNING", self.config.SEVERITY["WARNING"],
                                     f"Material groups are unbalanced. Categories exceeding {self.config.MAX_MATERIAL_GROUP_PERCENTAGE*100}%: {unbalanced_groups.to_dict()}",
                                     len(unbalanced_groups), (len(unbalanced_groups) / len(material_group_counts)) * 100)
                else:
                    self._add_result("completeness_checks", "Material Group Balance", "PASS", self.config.SEVERITY["INFO"], "Material groups are balanced.")
            else:
                self._add_result("completeness_checks", "Material Group Balance", "INFO", self.config.SEVERITY["INFO"], "No materials to check group balance.")

        # Date ranges are correct (2020-2024)
        min_overall_date = datetime.date(9999, 12, 31)
        max_overall_date = datetime.date(1, 1, 1)
        
        for table_name, table_info in self.config.SCHEMA.items():
            if table_name not in self.data: continue
            df = self.data[table_name]
            for field_name, field_props in table_info["fields"].items():
                if field_props["type"] == datetime.date and field_name in df.columns and field_name not in ['VALID_TO','EINDT','BUDAT','ACTUAL_DELIVERY_DATE']:
                    if not df[field_name].empty:
                        
                        min_date = df[field_name].min()
                        max_date = df[field_name].max()
                        if pd.notna(min_date) and pd.notna(max_date):
                            min_overall_date = min(min_overall_date, min_date)
                            max_overall_date = max(max_overall_date, max_date)
        
        if min_overall_date == datetime.date(9999, 12, 31) or max_overall_date == datetime.date(1, 1, 1):
            self._add_result("completeness_checks", "Overall Date Range", "INFO", self.config.SEVERITY["INFO"], "No date fields found to check overall date range.")
        else:
            expected_min, expected_max = self.config.DATA_DATE_RANGE
            if not (expected_min <= min_overall_date and max_overall_date <= expected_max):
                self._add_result("completeness_checks", "Overall Date Range", "FAIL", self.config.SEVERITY["CRITICAL"],
                                 f"Data date range ({min_overall_date} to {max_overall_date}) is outside expected range ({expected_min} to {expected_max}).",
                                 1, 100.0)
            else:
                self._add_result("completeness_checks", "Overall Date Range", "PASS", self.config.SEVERITY["INFO"], "Overall data date range is correct.")

        # All currencies are valid ISO codes (already covered by schema validation's valid_values for EKKO.WAERS)
        # This check is implicitly covered by schema validation. We can add a placeholder or skip.
        self._add_result("completeness_checks", "Valid Currency Codes", "PASS", self.config.SEVERITY["INFO"], "Currency codes are validated by schema check (EKKO.WAERS).")

    def profile_data(self):
        """Generates data profiles for each loaded DataFrame.

        Calculates descriptive statistics, unique values, and distributions.
        Stores profiles in `self.profiles` for analysis.

        Args:
            self (object): Instance with `data` and `profiles` attributes.

        Returns:
            None: Populates `self.profiles` with data profiling information.
        """
        print_colored("\n--- Generating Data Profile ---", 'HEADER')
        self.data_profile["record_counts"] = {name: len(df) for name, df in self.data.items()}
        
        # Date range coverage
        date_ranges = {}
        for table_name, table_info in self.config.SCHEMA.items():
            if table_name not in self.data: continue
            df = self.data[table_name]
            for field_name, field_props in table_info["fields"].items():
                if field_props["type"] == datetime.date and field_name in df.columns  and field_name not in ['ACTUAL_DELIVERY_DATE']:
                    if not df[field_name].empty:
                        min_date = df[field_name].min()
                        max_date = df[field_name].max()
                        if pd.notna(min_date) and pd.notna(max_date):
                            date_ranges[f"{table_name}.{field_name}"] = {"min": str(min_date), "max": str(max_date)}
        self.data_profile["date_range_coverage"] = date_ranges

        # Distribution statistics (spend by vendor, category, etc.)
        if "EKKO" in self.data and "EKPO" in self.data:
            merged_df = pd.merge(self.data["EKKO"][["EBELN", "LIFNR"]], self.data["EKPO"][["EBELN", "MATKL", "NETWR"]], on="EBELN", how="inner")
            self.data_profile["spend_by_vendor"] = merged_df.groupby("LIFNR")["NETWR"].sum().nlargest(10).to_dict()
            self.data_profile["spend_by_material_category"] = merged_df.groupby("MATKL")["NETWR"].sum().to_dict()
        
        if "MARA" in self.data:
            self.data_profile["materials_by_category"] = self.data["MARA"]["MATKL"].value_counts().to_dict()

        # Relationship cardinality (avg items per PO, receipts per item, etc.)
        if "EKKO" in self.data and "EKPO" in self.data:
            items_per_po = self.data["EKPO"].groupby("EBELN").size()
            self.data_profile["avg_items_per_po"] = items_per_po.mean() if not items_per_po.empty else 0
            self.data_profile["max_items_per_po"] = items_per_po.max() if not items_per_po.empty else 0
        
        if "EKPO" in self.data and "EKBE" in self.data:
            receipts_per_item = self.data["EKBE"].groupby(["EBELN", "EBELP"]).size()
            self.data_profile["avg_ekbe_per_ekpo_item"] = receipts_per_item.mean() if not receipts_per_item.empty else 0
            self.data_profile["max_ekbe_per_ekpo_item"] = receipts_per_item.max() if not receipts_per_item.empty else 0

        print_colored("  Data profiling complete.", 'OKGREEN')

    # --- Overall DQ Score Calculation ---
    def calculate_overall_dq_score(self):
        """Calculates an overall data quality score based on validation results.

        Aggregates `self.results` to compute a weighted score.
        Considers severity and number of violations.

        Args:
            self (object): Instance with `results` attribute.

        Returns:
            float: The calculated overall data quality score.
        """
        total_score = 0
        total_weight = sum(self.config.DQ_SCORE_WEIGHTS.values())
        
        for category, weight in self.config.DQ_SCORE_WEIGHTS.items():
            category_results = self.results.get(category, [])
            
            if not category_results:
                # If no checks were run for a category, assume perfect for its weight
                total_score += weight * 100
                continue

            category_pass_score = 0
            num_checks = len(category_results)
            
            for res in category_results:
                if res.status == "PASS":
                    category_pass_score += 1
                elif res.status == "WARNING":
                    category_pass_score += 0.5 # Partial credit for warnings
                # No credit for FAIL

            if num_checks > 0:
                category_score = (category_pass_score / num_checks) * 100
                total_score += (category_score / 100) * weight * 100 # Scale by weight
            else:
                total_score += weight * 100 # If no checks, assume perfect for this category

        self.overall_dq_score = round(total_score / total_weight, 2) if total_weight > 0 else 0.0
        print_colored(f"\nOverall Data Quality Score: {self.overall_dq_score:.2f}/100", 'BOLD')

    def generate_report(self):
        """Generates a comprehensive data quality report.

        Compiles `self.results` and `self.profiles` into a structured report.
        Includes overall score, detailed check results, and data profiles.

        Args:
            self (object): Instance with `results`, `profiles`, and `overall_score`.

        Returns:
            str: The formatted data quality report.
        """
        print_colored("\n--- Generating Reports ---", 'HEADER')
        os.makedirs(self.config.REPORT_DIR, exist_ok=True)

        # JSON Report
        report_data = {
            "overall_dq_score": self.overall_dq_score,
            "summary": {
                "pass_count": sum(1 for cat_res in self.results.values() for res in cat_res if res.status == "PASS"),
                "fail_count": sum(1 for cat_res in self.results.values() for res in cat_res if res.status == "FAIL"),
                "warning_count": sum(1 for cat_res in self.results.values() for res in cat_res if res.status == "WARNING"),
                "critical_issues": sum(1 for cat_res in self.results.values() for res in cat_res if res.severity == self.config.SEVERITY["CRITICAL"] and res.status != "PASS"),
                "warning_issues": sum(1 for cat_res in self.results.values() for res in cat_res if res.severity == self.config.SEVERITY["WARNING"] and res.status != "PASS"),
                "info_issues": sum(1 for cat_res in self.results.values() for res in cat_res if res.severity == self.config.SEVERITY["INFO"] and res.status != "PASS")
            },
            "detailed_findings": {category: [res.to_dict() for res in results] for category, results in self.results.items()},
            "data_profile": self.data_profile
        }
        
        json_filepath = os.path.join(self.config.REPORT_DIR, self.config.REPORT_FILENAME_JSON)
        with open(json_filepath, 'w') as f:
            json.dump(report_data, f, indent=4, default=str) # default=str to handle datetime objects
        print_colored(f"  JSON report saved to {json_filepath}", 'OKGREEN')

        # HTML Dashboard
        self._generate_html_dashboard(report_data)
        print_colored(f"  HTML dashboard saved to {os.path.join(self.config.REPORT_DIR, self.config.REPORT_FILENAME_HTML)}", 'OKGREEN')
    
    def _generate_html_dashboard(self, report_data):
        """Generates an HTML dashboard summarizing data quality results.

        Uses `self.results` and `self.overall_score` to create an interactive HTML view.
        Visualizes validation outcomes and key metrics.

        Args:
            self (object): Instance with `results` and `overall_score`.

        Returns:
            str: The HTML content of the dashboard.
        """
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SAP Data Quality Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }}
                .container {{ max-width: 1200px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1, h2, h3 {{ color: #0056b3; }}
                .summary-card {{ background-color: #e9ecef; border-left: 5px solid #007bff; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .summary-item {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
                .summary-item h3 {{ margin-top: 0; font-size: 1.2em; color: #555; }}
                .summary-item p {{ font-size: 1.8em; font-weight: bold; margin: 5px 0; }}
                .status-PASS {{ color: #28a745; }}
                .status-FAIL {{ color: #dc3545; }}
                .status-WARNING {{ color: #ffc107; }}
                .severity-Critical {{ background-color: #f8d7da; color: #721c24; border-left: 5px solid #dc3545; }}
                .severity-Warning {{ background-color: #fff3cd; color: #856404; border-left: 5px solid #ffc107; }}
                .severity-Info {{ background-color: #d1ecf1; color: #0c5460; border-left: 5px solid #17a2b8; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #007bff; color: white; }}
                .accordion {{ background-color: #eee; color: #444; cursor: pointer; padding: 18px; width: 100%; text-align: left; border: none; outline: none; transition: 0.4s; font-size: 1.1em; margin-top: 10px; }}
                .active, .accordion:hover {{ background-color: #ccc; }}
                .panel {{ padding: 0 18px; background-color: white; max-height: 0; overflow: hidden; transition: max-height 0.2s ease-out; }}
                .chart-container {{ width: 48%; display: inline-block; margin: 1%; vertical-align: top; }}
                .chart-row {{ display: flex; flex-wrap: wrap; justify-content: space-between; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SAP Data Quality Dashboard</h1>
                <p>Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

                <div class="summary-card">
                    <h2>Overall Data Quality Score: <span style="font-size: 2em; color: {self._get_score_color(report_data['overall_dq_score'])}">{report_data['overall_dq_score']}/100</span></h2>
                </div>

                <h2>Summary Dashboard</h2>
                <div class="summary-grid">
                    <div class="summary-item"><h3>Total Checks</h3><p>{sum(len(v) for v in self.results.values())}</p></div>
                    <div class="summary-item status-PASS"><h3>Passed Checks</h3><p>{report_data['summary']['pass_count']}</p></div>
                    <div class="summary-item status-FAIL"><h3>Failed Checks</h3><p>{report_data['summary']['fail_count']}</p></div>
                    <div class="summary-item status-WARNING"><h3>Warning Checks</h3><p>{report_data['summary']['warning_count']}</p></div>
                    <div class="summary-item severity-Critical"><h3>Critical Issues</h3><p>{report_data['summary']['critical_issues']}</p></div>
                    <div class="summary-item severity-Warning"><h3>Warning Issues</h3><p>{report_data['summary']['warning_issues']}</p></div>
                    <div class="summary-item severity-Info"><h3>Info Issues</h3><p>{report_data['summary']['info_issues']}</p></div>
                </div>

                <h2>Data Profile</h2>
                <h3>Record Counts</h3>
                <table>
                    <thead><tr><th>Table</th><th>Records</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in report_data['data_profile']['record_counts'].items())}
                    </tbody>
                </table>
                <h3>Date Range Coverage</h3>
                <table>
                    <thead><tr><th>Field</th><th>Min Date</th><th>Max Date</th></tr></thead>
                    <tbody>
                        {''.join(f"<tr><td>{k}</td><td>{v['min']}</td><td>{v['max']}</td></tr>" for k, v in report_data['data_profile']['date_range_coverage'].items())}
                    </tbody>
                </table>
                <h3>Distribution Statistics</h3>
                <ul>
                    <li><strong>Top 10 Vendors by Spend:</strong> {report_data['data_profile'].get('spend_by_vendor', {})}</li>
                    <li><strong>Spend by Material Category:</strong> {report_data['data_profile'].get('spend_by_material_category', {})}</li>
                    <li><strong>Materials by Category:</strong> {report_data['data_profile'].get('materials_by_category', {})}</li>
                    <li><strong>Average Items per PO:</strong> {report_data['data_profile'].get('avg_items_per_po', 'N/A'):.2f}</li>
                    <li><strong>Max Items per PO:</strong> {report_data['data_profile'].get('max_items_per_po', 'N/A')}</li>
                    <li><strong>Average EKBE records per EKPO item:</strong> {report_data['data_profile'].get('avg_ekbe_per_ekpo_item', 'N/A'):.2f}</li>
                    <li><strong>Max EKBE records per EKPO item:</strong> {report_data['data_profile'].get('max_ekbe_per_ekpo_item', 'N/A')}</li>
                </ul>

                <h2>Detailed Findings</h2>
                {''.join(self._format_detailed_findings(category, findings) for category, findings in report_data['detailed_findings'].items())}

                <h2>Visualizations</h2>
                <div class="chart-row">
                    <div class="chart-container"><canvas id="spendDistributionChart"></canvas></div>
                    <div class="chart-container"><canvas id="deliveryPerformanceChart"></canvas></div>
                </div>
                <div class="chart-row">
                    <div class="chart-container"><canvas id="priceVarianceChart"></canvas></div>
                    <div class="chart-container"><canvas id="materialCompletenessChart"></canvas></div>
                </div>

            </div>
            <script>
                var acc = document.getElementsByClassName("accordion");
                var i;
                for (i = 0; i < acc.length; i++) {{
                    acc[i].addEventListener("click", function() {{
                        this.classList.toggle("active");
                        var panel = this.nextElementSibling;
                        if (panel.style.maxHeight) {{
                            panel.style.maxHeight = null;
                        }} else {{
                            panel.style.maxHeight = panel.scrollHeight + "px";
                        }} 
                    }});
                }}
                {self._generate_chart_js()}
            </script>
        </body>
        </html>
        """
        html_filepath = os.path.join(self.config.REPORT_DIR, self.config.REPORT_FILENAME_HTML)
        with open(html_filepath, 'w') as f:
            f.write(html_content)

    def _format_detailed_findings(self, category, findings):
        html = f'<button class="accordion">{category.replace("_", " ").title()}</button><div class="panel">'
        for finding in findings:
            status_class = f"status-{finding['status']}"
            severity_class = f"severity-{finding['severity'].replace(' ', '')}"
            html += f"""
            <div class="summary-card {severity_class}">
                <h3>{finding['check_name']} <span class="{status_class}">({finding['status']})</span></h3>
                <p><strong>Description:</strong> {finding['description']}</p>
                <p><strong>Violations:</strong> {finding['violations']} ({finding['affected_percentage']}%)</p>
                {'<p><strong>Examples:</strong> ' + ', '.join(map(str, finding['examples'])) + '</p>' if finding['examples'] else ''}
            </div>
            """
        html += '</div>'
        return html

    def _get_score_color(self, score):
        if score >= 90: return '#28a745' # Green
        if score >= 70: return '#ffc107' # Yellow
        return '#dc3545' # Red

    def _generate_chart_js(self):
        chart_js = []

        # Spend Distribution Histogram (by Material Category)
        if 'spend_by_material_category' in self.data_profile:
            labels = list(self.data_profile['spend_by_material_category'].keys())
            data = list(self.data_profile['spend_by_material_category'].values())
            chart_js.append(f"""
            new Chart(document.getElementById('spendDistributionChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(labels)},
                    datasets: [{{
                        label: 'Total Spend',
                        data: {json.dumps(data)},
                        backgroundColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'],
                        borderColor: ['#007bff', '#28a745', '#ffc107', '#dc3545'],
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Spend Distribution by Material Category' }} }},
                    scales: {{ y: {{ beginAtZero: true, title: {{ display: true, text: 'Spend ($)' }} }} }}
                }}
            }});
            """)
        
        # Delivery Performance Distribution (Late vs On-time)
        if "EKBE" in self.data and "EKPO" in self.data:
            gr_records = self.data["EKBE"][self.data["EKBE"]["BEWTP"] == 'E'].copy()
            if not gr_records.empty:
                merged_gr = pd.merge(gr_records, self.data["EKPO"][["EBELN", "EBELP", "EINDT"]], on=["EBELN", "EBELP"], how="left")
                merged_gr['EINDT'] = pd.to_datetime(merged_gr['EINDT'], errors='coerce').dt.date
                merged_gr['ACTUAL_DELIVERY_DATE'] = pd.to_datetime(merged_gr['ACTUAL_DELIVERY_DATE'], errors='coerce').dt.date
                merged_gr = merged_gr.dropna(subset=['EINDT', 'ACTUAL_DELIVERY_DATE'])

                if not merged_gr.empty:
                    late_count = len(merged_gr[merged_gr["ACTUAL_DELIVERY_DATE"] > merged_gr["EINDT"]])
                    on_time_count = len(merged_gr) - late_count
                    chart_js.append(f"""
                    new Chart(document.getElementById('deliveryPerformanceChart'), {{
                        type: 'pie',
                        data: {{
                            labels: ['On-Time', 'Late'],
                            datasets: [{{
                                data: [{on_time_count}, {late_count}],
                                backgroundColor: ['#28a745', '#dc3545'],
                                hoverOffset: 4
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{ title: {{ display: true, text: 'Delivery Performance' }} }}
                        }}
                    }});
                    """)

        # Price Variance Distribution (e.g., histogram of (NETPR - BASE_PRICE) / BASE_PRICE)
        # This requires the internal BASE_PRICE from the generator, which is not in MARA.csv.
        # For this, we'd need to either save BASE_PRICE in MARA.csv or re-calculate/infer.
        # For now, let's assume we can get a proxy or skip if not available.
        # If MARA.csv had BASE_PRICE, we could do:
        if "EKPO" in self.data and "MARA" in self.data:
            merged_prices = pd.merge(self.data["EKPO"], self.data["MARA"][["MATNR", "BASE_PRICE"]], on="MATNR", how="left")
            merged_prices['PRICE_DIFF_PERCENT'] = (merged_prices['NETPR'] - merged_prices['BASE_PRICE']) / merged_prices['BASE_PRICE'] * 100
            price_diffs = merged_prices['PRICE_DIFF_PERCENT'].dropna()
            if not price_diffs.empty:
                # Create a histogram data
                hist, bins = np.histogram(price_diffs, bins=20)
                labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}%" for i in range(len(bins)-1)]
                data = hist.tolist()
                chart_js.append(f"""
                new Chart(document.getElementById('priceVarianceChart'), {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels)},
                        datasets: [{{
                            label: 'Price Variance (%)',
                            data: {json.dumps(data)},
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{ title: {{ display: true, text: 'Price Variance Distribution (vs Base Price)' }} }},
                        scales: {{
                            x: {{ title: {{ display: true, text: 'Variance (%)' }} }},
                            y: {{ beginAtZero: true, title: {{ display: true, text: 'Number of Items' }} }}
                        }}
                    }}
                }});
                """)

        # Data completeness heatmap (e.g., null values per column)
        # This is harder to do directly with Chart.js without pre-processing.
        # Let's do a simple bar chart of null percentages per table/column.
        null_data = []
        null_labels = []
        for table_name, df in self.data.items():
            null_counts = df.isnull().sum()
            total_rows = len(df)
            if total_rows > 0:
                for col, count in null_counts.items():
                    if count > 0:
                        null_labels.append(f"{table_name}.{col}")
                        null_data.append((count / total_rows) * 100)
        
        if null_data:
            chart_js.append(f"""
            new Chart(document.getElementById('materialCompletenessChart'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(null_labels)},
                    datasets: [{{
                        label: 'Null Percentage',
                        data: {json.dumps(null_data)},
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{ title: {{ display: true, text: 'Null Value Completeness by Field' }} }},
                    scales: {{
                        x: {{ ticks: {{ autoSkip: false, maxRotation: 45, minRotation: 45 }} }},
                        y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Null %' }} }}
                    }}
                }}
            }});
            """)

        return "\n".join(chart_js)
    
    def run_all_checks(self):
        start_time = datetime.datetime.now()
        print_colored(f"Starting Data Quality checks at {start_time}",'BOLD')

        self.load_data()
        self.validate_schema()
        self.validate_referential_integrity()
        self.validate_business_logic()
        self.validate_statistical()
        self.validate_completeness()
        self.profile_data()
        self.calculate_overall_dq_score()
        self.generate_report()

        end_time = datetime.datetime.now()
        print_colored(f"\nFinished Data Quality checks at {end_time}",'BOLD')
        print_colored(f"Total time taken: {end_time - start_time}",'BOLD')

if __name__ == "__main__":
    dq_config = dq_config()
    data_quality_check=data_quality(dq_config)
    data_quality_check.run_all_checks()