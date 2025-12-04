from faker import Faker
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
import numpy as np
from src.data_generator.config import Config
import  datetime 
from collections import defaultdict
import logging
from src.data_generator.utilities import (
    get_random_date, get_random_date_in_range, weighted_choice,
     calculate_net_value,generate_id, save_dataframe, log_normal_int,
    get_q4_multiplier, get_delivery_delay_days,_validate_configuration_variables
)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class SAPDataGenerator:
    def __init__(self,config):
        self.config=config
       
        self.fake=Faker()
        self.lfa1_df=None
        self.mara_df =None
        self.contract_df=None
        self.ekko_df=None
        self.ekpo_df =None
        self.ekbe_df=None
        self.material_base_prices = {}
        self.vendor_weights=None
        
        Faker.seed(self.config.RANDOM_SEED)
        random.seed(self.config.RANDOM_SEED)
        np.random.seed(self.config.RANDOM_SEED)



    def _calculate_vendor_weights(self ):
        logging.info(f"Calculating vendor weights ")
        try :
            _validate_configuration_variables(self,key_name='NUM_VENDORS',type=int,min_val=1)

            _validate_configuration_variables(self,key_name='VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES',type=float,min_val=0,max_val=1)

            _validate_configuration_variables(self,key_name='VENDOR_SALES_CONTRIBUTION_PERCENTAGE',type=float,min_val=0,max_val=1)
            top_vendor_percentage=self.config.VENDOR_PERCENTAGE_FOR_DISTRIBUTION_OF_SALES
            top_selection_percentage=self.config.VENDOR_SALES_CONTRIBUTION_PERCENTAGE
            num_top_vendors=int(top_vendor_percentage*self.config.NUM_VENDORS)
            top_vendor_weights=top_selection_percentage/num_top_vendors
            other_vendor_weight=(1-top_selection_percentage)/(self.config.NUM_VENDORS-num_top_vendors)
            weights = np.zeros(self.config.NUM_VENDORS)
            weights[:num_top_vendors] = top_vendor_weights
            weights[num_top_vendors:] = other_vendor_weight
            logging.info(f"Successfully calculated Vendor weights") 
            self.vendor_weights=weights
            return weights
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error calculating vendor weights: {e}", exc_info=True)
            raise # Re-raise the exception after logging
        except Exception as e:
            logging.critical(f"An unexpected error occurred during vendor weight calculation: {e}", exc_info=True)
            raise 


        
    def generate_lfa1(self):
        """
        Generates LFA1 (Vendor Master) data based on the provided configuration.

        This function creates a list of vendor dictionaries, each representing a vendor
        with various attributes like ID, name, address, and status. It incorporates
        randomness for blocking and preferred status, ensuring a controlled distribution
        of these attributes based on configured percentages.

        The generated data is then converted into a Pandas DataFrame and saved
        to a file as specified in the configuration.

        Attributes generated for each vendor:
        - LIFNR (Vendor ID): Unique identifier for the vendor.
        - NAME1 (Vendor Name): Company name.
        - LAND1 (Country Key): Country code.
        - ORT01 (City): City name.
        - KTOKK (Vendor Account Group): Type of vendor.
        - ERDAT (Date on which the record was created): Creation date.
        - STRAS (House number and street): Street address.
        - SMTP_ADDR (E-mail address): Vendor's email.
        - SPERR (Posting block for vendor): 'X' if blocked, ' ' otherwise.
        - IS_PREFERRED (Custom field): True if preferred, False otherwise.
        """
        logging.info("Starting LFA1 (Vendor Master) data generation.")
        last_id = None
        vendor_data = []
        is_blocked_count = 0
        is_prefered_count = 0

        try:
            _validate_configuration_variables(self,key_name='NUM_VENDORS',type=int,min_val=1)
            _validate_configuration_variables(self,key_name='VENDOR_BLOCKED_PERCENTAGE',type=float,max_val=1)
            _validate_configuration_variables(self,key_name='VENDOR_PREFERRED_PERCENTAGE',type=float,max_val=1)
           
            
            for i in range(self.config.NUM_VENDORS):
                blocked_ind = " "

                # Generate unique vendor ID
                vendor_ID = generate_id("V", last_id, 7)

                # Determine if vendor is blocked
                # Ensure blocked count does not exceed the configured percentage
                if (random.random() < self.config.VENDOR_BLOCKED_PERCENTAGE) and (is_blocked_count < (self.config.VENDOR_BLOCKED_PERCENTAGE * self.config.NUM_VENDORS)):
                    blocked_ind = "X"
                    is_blocked_count += 1
                    

                is_prefered = False
                # Determine if vendor is preferred
                # Ensure preferred count does not exceed the configured percentage
                if (random.random() < self.config.VENDOR_PREFERRED_PERCENTAGE) and (is_prefered_count < (self.config.VENDOR_PREFERRED_PERCENTAGE * self.config.NUM_VENDORS)):
                    is_prefered = True
                    is_prefered_count += 1
                    

                last_id = vendor_ID

                vendor_data.append({
                    'LIFNR': vendor_ID,
                    'NAME1': self.fake.company(),
                    'LAND1': self.fake.country_code(),
                    'ORT01': self.fake.city(),
                    'KTOKK': random.choice(self.config.VENDOR_TYPES),
                    'ERDAT': get_random_date(self.config.START_DATE, self.config.END_DATE),
                    'STRAS': self.fake.street_address(),
                    'SMTP_ADDR': self.fake.email(),
                    'SPERR': blocked_ind,
                    'IS_PREFERRED': is_prefered,
                })
                

            self.lfa1_df = pd.DataFrame(vendor_data)
            logging.info(f"Generated {len(self.lfa1_df)} vendor records.")
            logging.info(f"Blocked vendors: {is_blocked_count}, Preferred vendors: {is_prefered_count}")

            save_dataframe(self.lfa1_df, "LFA1.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            logging.info(f"LFA1 data successfully saved to {self.config.OUTPUT_DIR}/vendors.csv in {self.config.OUTPUT_FORMAT} format.")
            return self.lfa1_df
        except Exception as e:
            logging.error(f"An error occurred during LFA1 data generation: {e}", exc_info=True)
            self.lfa1_df = pd.DataFrame() # Ensure lfa1_df is an empty DataFrame on error
        
        
    def generate_mara(self):
        """
        Generates MARA (Material Master) data based on the provided configuration.

        This function creates a list of material dictionaries, each representing a material
        with various attributes like ID, description, type, weight, and base price.
        It uses predefined material groups, types, and units of measure from the
        configuration to generate realistic material data.

        The function also calculates gross and net weights, and assigns a base price
        within a specified range for each material group. The generated base prices
        are stored in `self.material_base_prices` for potential use in other functions.

        The generated data is then converted into a Pandas DataFrame and saved
        to a file as specified in the configuration.

        Attributes generated for each material:
        - MATNR (Material Number): Unique identifier for the material.
        - MAKTX (Material Description): Description of the material.
        - MTART (Material Type): Type of the material (e.g., FERT, ROH).
        - MATKL (Material Group): Group to which the material belongs.
        - MEINS (Base Unit of Measure): Unit of measure for the material.
        - ERSDA (Date on which the record was created): Creation date.
        - BRGEW (Gross Weight): Total weight including packaging.
        - NTGEW (Net Weight): Weight of the material itself, excluding packaging.
        - BASE_PRICE (Custom field): Base price of the material.

        """
        logging.info("Starting MARA (Material Master) data generation.")
        material_data = []
        last_id = None

        try:
            _validate_configuration_variables(self,key_name='NUM_MATERIALS',type=int,min_val=1)
            _validate_configuration_variables(self,key_name='MATERIAL_TYPES',type=list,num_type=str)
            _validate_configuration_variables(self,key_name='UNITS_OF_MEASURE',type=list,num_type=str)
            #_validate_configuration_variables(self,key_name='MATERIAL_GROUPS',type=list)
            

            for i in range(self.config.NUM_MATERIALS):
                mat_id = generate_id("M", last_id, 7)
                last_id = mat_id

                mat_group = random.choice(list(self.config.MATERIAL_GROUPS.keys()))
                mat_desc = random.choice(self.config.MATERIAL_GROUPS[mat_group]["Description"])
                mat_type = random.choice(self.config.MATERIAL_TYPES)
                mat_ut_mes = random.choice(self.config.UNITS_OF_MEASURE)

                # Determine material weight based on unit of measure
                mat_wt = 0.0
                if mat_ut_mes == 'KG':
                    mat_wt = round(random.uniform(0.1, 100.0), 2)
                elif mat_ut_mes == 'M':
                    mat_wt = round(random.uniform(0.01, 5.0), 2)
                elif mat_ut_mes == 'PC' or mat_ut_mes == 'EA':
                    mat_wt = round(random.uniform(0.001, 50.0), 3)
                else:  # Default for others
                    mat_wt = round(random.uniform(0.05, 20.0), 2)

                # Calculate net weight by applying a random tare percentage
                tare_percentage = random.uniform(0.01, 0.10)
                mat_net_wt = round(mat_wt * (1 - tare_percentage), 3)
                if mat_net_wt < 0:
                    mat_net_wt = 0  # Ensure net weight is not negative

                # Assign base price based on material group's price range
                price_range = self.config.MATERIAL_GROUPS[mat_group]['price_range']
                base_price = round(random.uniform(price_range[0], price_range[1]), 2)
                self.material_base_prices[mat_id] = base_price # Store base price for this material

                material_data.append({
                    'MATNR': mat_id,
                    'MAKTX': mat_desc,
                    'MTART': mat_type,
                    'MATKL': mat_group,
                    'MEINS': mat_ut_mes,
                    'ERSDA': get_random_date(self.config.START_DATE, self.config.END_DATE),
                    'BRGEW': mat_wt,
                    'NTGEW': mat_net_wt,
                    'BASE_PRICE': base_price,
                })
                

            self.mara_df = pd.DataFrame(material_data)
            logging.info(f"Generated {len(self.mara_df)} material records.")

            save_dataframe(self.mara_df, "MARA.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            logging.info(f"MARA data successfully saved to {self.config.OUTPUT_DIR}/material.csv in {self.config.OUTPUT_FORMAT} format.")
            return self.mara_df

        except Exception as e:
            logging.error(f"An error occurred during MARA data generation: {e}", exc_info=True)
            self.mara_df = pd.DataFrame() # Ensure mara_df is an empty DataFrame on error
       

    def generate_vendor_contract(self):
        """
        Generates vendor contract data based on existing vendor (LFA1) and material (MARA) data.

        This function creates contracts between active vendors and materials. It first
        identifies active vendors (not blocked) and all available materials.
        It then randomly selects a subset of possible vendor-material combinations
        to create contracts, based on the `CONTRACT_COVERAGE_PERCENTAGE` configuration.

        For each selected combination, it generates contract details such as:
        - CONTRACT_ID: Unique identifier for the contract.
        - LIFNR: Vendor ID.
        - MATNR: Material ID.
        - CONTRACT_PRICE: Price, calculated as a discount from the material's base price.
        - VALID_FROM: Start date of the contract.
        - VALID_TO: End date of the contract.
        - VOLUME_COMMITMENT: Agreed-upon volume.
        - CONTRACT_TYPE: Type of contract.

        A percentage of contracts are intentionally made expired based on
        `EXPIRED_CONTRACT_PERCENTAGE` configuration.

        The generated data is then converted into a Pandas DataFrame and saved
        to a file as specified in the configuration.

        Prerequisites:
        - `self.lfa1_df` must be populated with vendor data (e.g., by calling `generate_lfa1`).
        - `self.mara_df` must be populated with material data (e.g., by calling `generate_mara`).
        - `self.material_base_prices` must contain base prices for materials.

        """
        logging.info("Starting Vendor Contract data generation.")
        contracts = []
        last_id = None

       
        _validate_configuration_variables(self,key_name='CONTRACT_COVERAGE_PERCENTAGE',type=tuple,num_type=float,max_val=1)
        _validate_configuration_variables(self,key_name='CONTRACT_VALIDITY_YEARS',type=tuple,num_type=int)
        _validate_configuration_variables(self,key_name='VOLUME_COMMITMENT_UNITS',type=tuple,num_type=int)
        _validate_configuration_variables(self,key_name='CONTRACT_PRICE_DISCOUNT_PERCENTAGE',type=tuple,num_type=float,max_val=1)
        _validate_configuration_variables(self,key_name='EXPIRED_CONTRACT_PERCENTAGE',type=float,max_val=1)
        _validate_configuration_variables(self,key_name='START_DATE',type=datetime.date)
        _validate_configuration_variables(self,key_name='END_DATE',type=datetime.date)
        
        _validate_configuration_variables(self,key_name='CONTRACT_TYPES',type=list,num_type=str)
        _validate_configuration_variables(self,key_name='NUM_CONTRACTS_TARGET',type=int,min_val=1)
        
        
        if self.lfa1_df.empty or self.mara_df.empty:
            logging.error("LFA1 or MARA dataframes are empty. Cannot generate vendor contracts.")
            self.contract_df = pd.DataFrame()
            return

        try:
            # Filter for active vendors (not blocked)
            active_vendors = self.lfa1_df[self.lfa1_df['SPERR'] != 'X']['LIFNR'].tolist()
            if not active_vendors:
                logging.warning("No active vendors found to create contracts. Skipping contract generation.")
                self.contract_df = pd.DataFrame()
                return

            material_ids = self.mara_df['MATNR'].tolist()
            if not material_ids:
                logging.warning("No materials found to create contracts. Skipping contract generation.")
                self.contract_df = pd.DataFrame()
                return

            # Create all possible active vendor-material combinations
            all_combinations = [(v, m) for v in active_vendors for m in material_ids]
            logging.debug(f"Total possible vendor-material combinations: {len(all_combinations)}")

            # Determine how many combinations will have contracts
            min_coverage, max_coverage = self.config.CONTRACT_COVERAGE_PERCENTAGE
            num_combinations_with_contracts = int(len(all_combinations) * random.uniform(min_coverage, max_coverage))
            num_combinations_with_contracts = min(num_combinations_with_contracts, len(all_combinations)) # Cap at total combinations
            logging.info(f"Targeting {num_combinations_with_contracts} vendor-material combinations for contracts.")

            # Randomly select combinations for contracts
            contract_combinations = random.sample(all_combinations, num_combinations_with_contracts)

            for vendor_id, mat_id in contract_combinations:
                contract_id = generate_id("C", last_id, 5)
                last_id = contract_id

                # Generate valid_from and valid_to dates
                valid_from = get_random_date(self.config.START_DATE, self.config.END_DATE - datetime.timedelta(days=365))
                # Ensure valid_to is after valid_from
                valid_to = valid_from + datetime.timedelta(days=random.randint(*self.config.CONTRACT_VALIDITY_YEARS) * 365)

                # Introduce expired contracts
                if random.random() < self.config.EXPIRED_CONTRACT_PERCENTAGE:
                    # Set valid_to to a date in the past
                    valid_to = get_random_date(self.config.START_DATE, datetime.date.today() - datetime.timedelta(days=30))
                    # Ensure valid_from is before valid_to for expired contracts
                    valid_from = valid_to - datetime.timedelta(days=random.randint(*self.config.CONTRACT_VALIDITY_YEARS) * 365)
                    # Ensure valid_from is not before the overall START_DATE
                    if valid_from < datetime.datetime.strptime(str(self.config.START_DATE), '%Y-%m-%d').date():
                        valid_from = datetime.datetime.strptime(str(self.config.START_DATE), '%Y-%m-%d').date()
                    

                volume_commitment = random.randint(*self.config.VOLUME_COMMITMENT_UNITS)
                contract_type = random.choice(self.config.CONTRACT_TYPES)

                # Contract price: 5-15% below market average (material base price)
                base_price = self.material_base_prices.get(mat_id, 100.0) # Default to 100 if base price not found
                if base_price == 100.0:
                    logging.warning(f"Base price not found for material {mat_id}. Using default 100 for contract price calculation.")

                min_discount, max_discount = self.config.CONTRACT_PRICE_DISCOUNT_PERCENTAGE
                discount = random.uniform(min_discount, max_discount)
                contract_price = round(base_price * (1 - discount), 2)
                if contract_price <= 0: contract_price = round(base_price * 0.01, 2) # Ensure price is positive

                contracts.append({
                    'CONTRACT_ID': contract_id,
                    'LIFNR': vendor_id,
                    'MATNR': mat_id,
                    'CONTRACT_PRICE': contract_price,
                    'VALID_FROM': valid_from ,
                    'VALID_TO': valid_to,
                    'VOLUME_COMMITMENT': volume_commitment,
                    'CONTRACT_TYPE': contract_type
                })
                

                # Stop if target number of contracts is reached
                if len(contracts) >= self.config.NUM_CONTRACTS_TARGET:
                    logging.info(f"Reached target number of contracts ({self.config.NUM_CONTRACTS_TARGET}). Stopping generation.")
                    break

            self.contract_df = pd.DataFrame(contracts)
            logging.info(f"Generated {len(self.contract_df)} vendor contract records.")

            save_dataframe(self.contract_df, "vendor_contract.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            logging.info(f"Vendor Contract data successfully saved to {self.config.OUTPUT_DIR}/vendor_contract.csv in {self.config.OUTPUT_FORMAT} format.")

        except Exception as e:
            logging.error(f"An error occurred during Vendor Contract data generation: {e}", exc_info=True)
            self.contract_df = pd.DataFrame() # Ensure contract_df is an empty DataFrame on error
        

        

    def generate_ekko(self):
        """
        Generates EKKO (Purchase Order Header) data based on the provided configuration
        and existing vendor data.

        This function creates purchase order headers, assigning attributes such as
        PO number, company code, document type, creation date, vendor, currency,
        purchasing organization, and purchasing group.

        Key features:
        - Filters out blocked vendors from `self.lfa1_df` for PO creation.
        - Selects vendors based on a weighted distribution (`self.vendor_weights`),
          simulating a Pareto principle where a few vendors account for most POs.
        - Differentiates between 'Contract POs' (BSART='NB') and 'Standard POs' (BSART='FO')
          based on `CONTRACT_PO_PERCENTAGE`.
        - Generates creation dates (`AEDAT`) within the configured date range.
        - Includes a placeholder for seasonal patterns (Q4 multiplier), though its
          direct effect on the *number* of POs is noted as an area for refinement
          in this specific implementation.

        The generated data is then converted into a Pandas DataFrame and saved
        to a file as specified in the configuration.

        Prerequisites:
        - `self.lfa1_df` must be populated with vendor data (e.g., by calling `generate_lfa1`).
        - `self.vendor_weights` must be populated with weights corresponding to vendors
          in `self.lfa1_df`.

        """
        logging.info("Starting EKKO (Purchase Order Headers) data generation.")
        ekko_records = []
        last_id = None
        _validate_configuration_variables(self,key_name='CONTRACT_PO_PERCENTAGE',type=tuple,num_type=float,max_val=1)
        _validate_configuration_variables(self,key_name='NUM_PO_HEADERS',type=int,min_val=1)
        _validate_configuration_variables(self,key_name='COMPANY_CODES',type=list,num_type=str)
        _validate_configuration_variables(self,key_name='Q4_SPEND_INCREASE_PERCENTAGE',type=float,max_val=1)
        _validate_configuration_variables(self,key_name='START_DATE',type=datetime.date)
        _validate_configuration_variables(self,key_name='END_DATE',type=datetime.date)

        if self.lfa1_df.empty:
            logging.error("LFA1 dataframe is empty. Cannot generate EKKO data.")
            self.ekko_df = pd.DataFrame()
            return
        if  self.vendor_weights is  None or len(self.vendor_weights) != len(self.lfa1_df):
            logging.error("Vendor weights are not properly initialized or do not match LFA1_df length. Cannot generate EKKO data.")
            self.ekko_df = pd.DataFrame()
            return

        try:
            # Filter out blocked vendors for POs
            active_vendors_df = self.lfa1_df[self.lfa1_df['SPERR'] != 'X']
            active_vendor_lifnrs = active_vendors_df['LIFNR'].tolist()

            if not active_vendor_lifnrs:
                logging.warning("No active vendors found to create purchase orders. Skipping EKKO generation.")
                self.ekko_df = pd.DataFrame()
                return

            # Prepare vendor weights for selection (Pareto principle)
            # Map LIFNR to its pre-calculated weight
            vendor_lifnr_to_weight = {
                self.lfa1_df.loc[i, 'LIFNR']: self.vendor_weights[i]
                for i in range(len(self.lfa1_df))
                if self.lfa1_df.loc[i, 'SPERR'] != 'X'
            }

            # Filter weights for active vendors and ensure they are in the same order as active_vendor_lifnrs
            # This assumes self.vendor_weights is aligned with self.lfa1_df's original index
            active_vendor_weights_list = []
            for lifnr in active_vendor_lifnrs:
                active_vendor_weights_list.append(vendor_lifnr_to_weight.get(lifnr, 0)) # Use .get() with default 0 for safety

            active_vendor_weights = np.array(active_vendor_weights_list)
            # Re-normalize if necessary after filtering
            if np.sum(active_vendor_weights) == 0:
                logging.warning("All active vendor weights are zero. Assigning equal weights for PO generation.")
                active_vendor_weights = np.ones(len(active_vendor_lifnrs))
            active_vendor_weights = active_vendor_weights / np.sum(active_vendor_weights)
            logging.debug(f"Active vendor weights prepared for {len(active_vendor_lifnrs)} vendors.")

            # Determine number of contract vs non-contract POs
            
            
            min_contract_po_pct, max_contract_po_pct = self.config.CONTRACT_PO_PERCENTAGE
            num_contract_pos = int(self.config.NUM_PO_HEADERS * random.uniform(min_contract_po_pct, max_contract_po_pct))
            
            logging.info(f"Targeting {num_contract_pos} contract POs out of {self.config.NUM_PO_HEADERS} total POs.")

            for i in range(self.config.NUM_PO_HEADERS):
                ebeln = generate_id('PO', last_id, 10) # Assuming 10-char PO number
                last_id = ebeln

                bukrs = random.choice(self.config.COMPANY_CODES)

                # Decide if it's a contract PO or non-contract PO
                # 'NB' for standard PO, 'FO' for framework order (contract PO)
                # This logic might be inverted depending on SAP system configuration.
                # Assuming 'NB' is standard and 'FO' is for contracts/frameworks.
                bsart = 'NB' if i < num_contract_pos else 'FO'

                aedat = get_q4_multiplier(self.config.Q4_SPEND_INCREASE_PERCENTAGE,self.config.START_DATE, self.config.END_DATE)


                # Select vendor based on Pareto distribution
                lifnr = weighted_choice(active_vendor_lifnrs, active_vendor_weights)

                waers = random.choice(self.config.CURRENCIES)
                ekorg = random.choice(self.config.PURCHASING_ORGANIZATIONS)
                ekgrp = random.choice(self.config.PURCHASING_GROUPS)
                bedat = aedat # Document date usually same as PO date

                ekko_records.append({
                    'EBELN': ebeln,
                    'BUKRS': bukrs,
                    'BSART': bsart,
                    'AEDAT': aedat,
                    'LIFNR': lifnr,
                    'WAERS': waers,
                    'EKORG': ekorg,
                    'EKGRP': ekgrp,
                    'BEDAT': bedat
                })
                logging.debug(f"Generated EKKO record for PO {ebeln} (Vendor: {lifnr}, Type: {bsart}).")

            self.ekko_df = pd.DataFrame(ekko_records)
            logging.info(f"Generated {len(self.ekko_df)} EKKO (Purchase Order Header) records.")

            save_dataframe(self.ekko_df, "EKKO.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            logging.info(f"EKKO data successfully saved to {self.config.OUTPUT_DIR}/purchase_order.csv in {self.config.OUTPUT_FORMAT} format.")

        except Exception as e:
            logging.error(f"An error occurred during EKKO data generation: {e}", exc_info=True)
            self.ekko_df = pd.DataFrame() # Ensure ekko_df is an empty DataFrame on error
        finally:
            logging.info("Finished EKKO (Purchase Order Headers) data generation.")


    def generate_ekpo(self):
        """
        Generates EKPO (Purchase Order Line Item) data based on existing PO headers (EKKO),
        material master (MARA), vendor master (LFA1), and vendor contracts.

        This function iterates through each purchase order header and generates a variable
        number of line items for it. For each line item, it determines:
        - EBELN (PO Number) and EBELP (Line Item Number).
        - MATNR (Material Number), MATKL (Material Group), MEINS (Unit of Measure).
        - MENGE (Quantity) and NETPR (Net Price).
        - NETWR (Net Value) calculated from quantity and price.
        - EINDT (Expected Delivery Date).
        - WERKS (Plant).

        Key features:
        - Uses `log_normal_int` to generate a realistic distribution of line items per PO.
        - Determines `unit_price` based on a hierarchy:
            1. Active contract price if available and PO type is 'NB' (standard PO).
            2. Preferred vendor discount if the vendor is preferred.
            3. Price volatility applied to the material's base price.
            4. Handles 'FO' (framework order) POs that might deviate from contract price
               if an active contract exists but the purchase is off-contract.
        - Looks up vendor preferred status from `self.lfa1_df`.
        - Looks up material base prices and other details from `self.mara_df`.
        - Looks up contract details from `self.contract_df`.

        The generated data is then converted into a Pandas DataFrame and saved
        to a file as specified in the configuration.

        Prerequisites:
        - `self.ekko_df` must be populated with PO header data.
        - `self.mara_df` must be populated with material master data.
        - `self.lfa1_df` must be populated with vendor master data.
        - `self.contract_df` must be populated with vendor contract data.

        
        """
        logging.info("Starting EKPO (Purchase Order Line Items) data generation.")
        ekpo_records = []
        

        if self.ekko_df.empty:
            logging.error("EKKO dataframe is empty. Cannot generate EKPO data.")
            self.ekpo_df = pd.DataFrame()
            return
        if self.mara_df.empty:
            logging.error("MARA dataframe is empty. Cannot generate EKPO data.")
            self.ekpo_df = pd.DataFrame()
            return
        if self.lfa1_df.empty:
            logging.error("LFA1 dataframe is empty. Cannot generate EKPO data.")
            self.ekpo_df = pd.DataFrame()
            return

        _validate_configuration_variables(self,key_name='PREFERRED_VENDOR_DISCOUNT_PERCENTAGE',type=tuple,num_type=float,max_val=1)
        _validate_configuration_variables(self,key_name='PRICE_VOLATILITY_PERCENTAGE',type=float,max_val=1)
        _validate_configuration_variables(self,key_name='NUM_PO_LINE_ITEMS_TARGET',type=int,min_val=1)
        _validate_configuration_variables(self,key_name='PLANTS',type=list,num_type=str)

        try:
            # Pre-process contracts for quick lookup: (LIFNR, MATNR) -> list of contract rows
            contract_lookup = defaultdict(list)
            if not self.contract_df.empty:
                # Convert date columns to datetime objects for comparison
                self.contract_df['VALID_FROM'] = pd.to_datetime(self.contract_df['VALID_FROM']).dt.date
                self.contract_df['VALID_TO'] = pd.to_datetime(self.contract_df['VALID_TO']).dt.date
                for _, row in self.contract_df.iterrows():
                    contract_lookup[(row['LIFNR'], row['MATNR'])].append(row)
            logging.debug(f"Contract lookup table built with {len(contract_lookup)} unique vendor-material combinations.")
            
            # Pre-process vendor preferred status for quick lookup
            vendor_preferred_lookup = self.lfa1_df.set_index('LIFNR')['IS_PREFERRED'].to_dict()
            logging.debug(f"Vendor preferred status lookup built for {len(vendor_preferred_lookup)} vendors.")

            line_item_count = 0
            for idx, po_header in self.ekko_df.iterrows():
                # Convert PO header AEDAT to date object for comparison
                po_aedat = pd.to_datetime(po_header['AEDAT']).date()

                num_line_items = log_normal_int(
                    self.config.LINE_ITEMS_PER_PO_MEAN,
                    std_dev_factor=0.5,
                    min_val=1,
                    max_val=self.config.LINE_ITEMS_PER_PO_MAX
                )
                logging.debug(f"PO {po_header['EBELN']} will have {num_line_items} line items.")

                for i in range(num_line_items):
                    if line_item_count >= self.config.NUM_PO_LINE_ITEMS_TARGET:
                        logging.info(f"Reached target number of PO line items ({self.config.NUM_PO_LINE_ITEMS_TARGET}). Stopping generation.")
                        break

                    ebeln = po_header['EBELN']
                    ebelp = "LI"+str(i + 1).zfill(5) # Line item number (e.g., 00010, 00020)

                    # Select a material randomly
                    matnr_row = self.mara_df.sample(1).iloc[0]
                    matnr = matnr_row['MATNR']
                    matkl = matnr_row['MATKL']
                    meins = matnr_row['MEINS']
                    base_price = matnr_row['BASE_PRICE']

                    # Determine unit price based on contract, preferred vendor, and volatility
                    unit_price = base_price

                    # Check for active contract
                    active_contract = None
                    contracts_for_vm = contract_lookup.get((po_header['LIFNR'], matnr), [])
                    for contract in contracts_for_vm:
                        if contract['VALID_FROM'] <= po_aedat <= contract['VALID_TO']:
                            active_contract = contract
                            logging.debug(f"Found active contract for {po_header['LIFNR']}-{matnr} for PO {ebeln}.")
                            break

                    if active_contract is not None and po_header['BSART'] == 'NB': # Framework Order (Contract PO)
                        unit_price = active_contract['CONTRACT_PRICE']
                        logging.debug(f"PO {ebeln} (Type FO) uses contract price: {unit_price}.")
                    else: # Non-contract PO (BSART='FO') or no active contract
                        # Apply preferred vendor discount if applicable
                        if vendor_preferred_lookup.get(po_header['LIFNR'], False):
                            min_discount, max_discount = self.config.PREFERRED_VENDOR_DISCOUNT_PERCENTAGE
                            discount = random.uniform(min_discount, max_discount)
                            unit_price *= (1 - discount)
                            logging.debug(f"Applied preferred vendor discount for {po_header['LIFNR']}. New price: {unit_price}.")

                        # Apply price volatility
                        volatility_factor = 1 + random.uniform(-self.config.PRICE_VOLATILITY_PERCENTAGE, self.config.PRICE_VOLATILITY_PERCENTAGE)
                        unit_price *= volatility_factor
                        logging.debug(f"Applied price volatility. New price: {unit_price}.")

                        # If there was an active contract but this is an 'NB' PO (standard PO)
                        # and the price is higher, reflect that variance (off-contract purchase).
                        # This scenario implies a deviation from the contract.
                        if active_contract is not None and po_header['BSART'] == 'FO' and unit_price < active_contract['CONTRACT_PRICE']:
                            # Make it higher than contract price to simulate off-contract purchase
                            unit_price = active_contract['CONTRACT_PRICE'] * random.uniform(1.05, 1.20) # 5-20% higher than contract
                            logging.warning(f"PO {ebeln} (Type NB) for {matnr} has active contract but price {unit_price} is higher than contract price {active_contract['CONTRACT_PRICE']}. Simulating off-contract purchase.")

                    unit_price = round(unit_price, 2)
                    if unit_price <= 0: unit_price = round(base_price * 0.01, 2) # Ensure price is positive

                    menge = random.randint(1, 1000) # Quantity
                    netwr = calculate_net_value(menge, unit_price)

                    # Expected delivery date: 7-60 days after PO date
                    eindt = get_random_date_in_range(po_aedat, 7, 60)

                    werks = random.choice(self.config.PLANTS)

                    ekpo_records.append({
                        'EBELN': ebeln,
                        'EBELP': ebelp,
                        'MATNR': matnr,
                        'MENGE': menge,
                        'MEINS': meins,
                        'NETPR': unit_price,
                        'NETWR': netwr,
                        'EINDT': eindt,#.strftime('%Y-%m-%d'), # Format date
                        'WERKS': werks,
                        'MATKL': matkl,
                        'LIFNR': po_header['LIFNR'], # For EKBE generation
                        'PO_DATE': po_header['AEDAT'] # For EKBE generation
                    })
                    line_item_count += 1
                if line_item_count >= self.config.NUM_PO_LINE_ITEMS_TARGET:
                    break

            self.ekpo_df = pd.DataFrame(ekpo_records)
            logging.info(f"Generated {len(self.ekpo_df)} EKPO (Purchase Order Line Item) records.")

            save_dataframe(self.ekpo_df, "EKPO.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            logging.info(f"EKPO data successfully saved to {self.config.OUTPUT_DIR}/purchase_order_line_item.csv in {self.config.OUTPUT_FORMAT} format.")

        except Exception as e:
            logging.error(f"An error occurred during EKPO data generation: {e}", exc_info=True)
            self.ekpo_df = pd.DataFrame() # Ensure ekpo_df is an empty DataFrame on error
        
    
    def generate_ekbe(self):
        """
        Generates synthetic data for the EKBE table (Purchase Order History).

        This function simulates goods receipts (BEWTP='E') and invoice receipts (BEWTP='Q') 
        based on existing purchase orders (EKKO/EKPO), material masters (MARA), and 
        vendor data (LFA1). It uses configuration parameters to simulate realistic 
        delivery delays and invoice frequency.

        Side Effects:
            - Validates configuration parameters using `_validate_configuration_variables`.
            - Updates `self.ekbe_df` with the generated DataFrame.
            - Logs errors via the logging module if input dataframes are empty or if 
            an exception occurs during generation.
            - Saves the resulting DataFrame to a file (CSV or specified format) 
            using `save_dataframe`.

        Raises:
            ValueError: If essential configuration variables are missing or invalid
                        (raised by the helper `_validate_configuration_variables`).
            Exception: Catches and logs general exceptions during generation process."""
        print("Generating EKBE (PO History)...")
        _validate_configuration_variables(self,key_name='LATE_DELIVERY_PERCENTAGE',type=tuple,num_type=float,max_val=1)
        _validate_configuration_variables(self,key_name='NUM_PO_HISTORY_TARGET',type=int,min_val=1)
        _validate_configuration_variables(self,key_name='VENDOR_PERFORMANCE_VARIATION',type=float,max_val=1)
        #_validate_configuration_variables(self,key_name='DELAY_DISTRIBUTION',type=tuple,num_type=float,max_val=1)
        
        
        
        
        ekbe_records = []
        if self.ekko_df.empty:
            logging.error("EKKO dataframe is empty. Cannot generate EKKO data.")
            self.ekpo_df = pd.DataFrame()
            return
        if self.mara_df.empty:
            logging.error("MARA dataframe is empty. Cannot generate EKKO data.")
            self.ekpo_df = pd.DataFrame()
            return
        if self.lfa1_df.empty:
            logging.error("LFA1 dataframe is empty. Cannot generate EKKO data.")
            self.ekpo_df = pd.DataFrame()
            return
        if self.lfa1_df.empty:
            logging.error("EKPO dataframe is empty. Cannot generate EKKO data.")
            self.ekpo_df = pd.DataFrame()
            return
        
        try:
        # Pre-process vendor performance for delivery delays
            vendor_delivery_performance = {}  # LIFNR -> average_late_rate_multiplier
            active_vendors = self.lfa1_df[self.lfa1_df['SPERR'] != 'X']['LIFNR'].tolist()
            for lifnr in active_vendors:
                base_late_rate = random.uniform(*self.config.LATE_DELIVERY_PERCENTAGE)
                performance_factor = 1 + random.uniform(-self.config.VENDOR_PERFORMANCE_VARIATION, self.config.VENDOR_PERFORMANCE_VARIATION)
                vendor_delivery_performance[lifnr] = max(0, min(1, base_late_rate * performance_factor))

            ekbe_count = 0
            gr_id_counter = 0
            inv_id_counter = 0

            for idx, po_item in self.ekpo_df.iterrows():
                if ekbe_count >= self.config.NUM_PO_HISTORY_TARGET:
                    break

                ebeln = po_item['EBELN']
                ebelp = po_item['EBELP']
                po_date = po_item['PO_DATE']
                eindt = po_item['EINDT']
                lifnr = po_item['LIFNR']
                total_po_menge = po_item['MENGE']
                netpr_per_unit = po_item['NETPR']

                # --- Determine number of GRs and their quantities (using internal logic) ---
                # For simplicity, let's say 1 to 3 GR splits for a PO item
                # More complex logic could be based on total_po_menge (e.g., larger quantities -> more splits)
                num_gr_splits = random.randint(1, 3) # Fixed internal range for splits
                
                gr_quantities = []
                remaining_menge = total_po_menge

                for i in range(num_gr_splits):
                    if i == num_gr_splits - 1: # Last split gets remaining quantity
                        gr_quantities.append(remaining_menge)
                    else:
                        # Distribute remaining quantity, ensuring at least 1 unit per split
                        # And not taking more than 80% of remaining to leave some for next splits
                        qty = random.randint(1, max(1, int(remaining_menge * 0.8 / (num_gr_splits - i))))
                        gr_quantities.append(qty)
                        remaining_menge -= qty
                
                # Final adjustment to ensure sum matches total_po_menge and no zero quantities
                gr_quantities = [q for q in gr_quantities if q > 0] # Remove any zero quantities
                if sum(gr_quantities) != total_po_menge:
                    if gr_quantities: # If there are still quantities
                        gr_quantities[-1] += (total_po_menge - sum(gr_quantities))
                        gr_quantities[-1] = max(1, gr_quantities[-1]) # Ensure last quantity is at least 1
                    else: # If all quantities became zero, just add the total_po_menge as one GR
                        gr_quantities = [total_po_menge]
                
                num_gr_splits = len(gr_quantities) # Update num_gr_splits after adjustments

                # --- Generate GRs and corresponding INVs ---
                gr_dates = []
                for i, gr_menge in enumerate(gr_quantities):
                    if gr_menge <= 0: continue # Skip if quantity is zero

                    # Determine if delivery is late
                    vendor_late_rate = vendor_delivery_performance.get(lifnr, np.mean(self.config.LATE_DELIVERY_PERCENTAGE))
                    days_to_delivery = (eindt - po_date).days
                    adjusted_late_rate = vendor_late_rate * (1 - (0.5 * (60 - days_to_delivery) / 53))
                    adjusted_late_rate = max(0, min(1, adjusted_late_rate))
                    is_late = random.random() < adjusted_late_rate

                    actual_delivery_date = eindt
                    if is_late:
                        delay_days = get_delivery_delay_days(self.config.DELAY_DISTRIBUTION)
                        actual_delivery_date = eindt + datetime.timedelta(days=delay_days)
                    
                    # Ensure actual delivery date is not before PO date
                    if actual_delivery_date < po_date:
                        actual_delivery_date = po_date + datetime.timedelta(days=1)
                    
                    # For subsequent GRs, make them later than the previous one
                    #if i > 0:
                       # actual_delivery_date = max(actual_delivery_date, gr_dates[-1] + datetime.timedelta(days=random.randint(1, 5)))
                    
                    gr_dates.append(actual_delivery_date)
                    gr_id_counter += 1
                    
                    ekbe_records.append({
                        'EBELN': ebeln,
                        'EBELP': ebelp,
                        'BEWTP': 'E', # Goods Receipt
                        'BUDAT': actual_delivery_date,
                        'MENGE': gr_menge,
                        'DMBTR': calculate_net_value(gr_menge, netpr_per_unit),
                        'BELNR': f"GR{gr_id_counter:05d}",
                        'ACTUAL_DELIVERY_DATE': actual_delivery_date
                    })
                    ekbe_count += 1

                    # --- Generate corresponding Invoice Receipt (BEWTP='Q') ---
                    # Aim for roughly 1:1 GR to INV ratio, with some internal variation
                    # Let's say 90% chance of an invoice for each GR
                    if random.random() < 1: # Fixed internal probability for invoice generation
                        if ekbe_count >= self.config.NUM_PO_HISTORY_TARGET:
                            break

                        invoice_date = get_random_date_in_range(actual_delivery_date, *self.config.INVOICE_DAYS_AFTER_GR)
                        inv_id_counter += 1

                        ekbe_records.append({
                            'EBELN': ebeln,
                            'EBELP': ebelp,
                            'BEWTP': 'Q', # Invoice Receipt
                            'BUDAT': invoice_date,
                            'MENGE': gr_menge, # Invoice quantity matches this GR
                            'DMBTR': calculate_net_value(gr_menge, netpr_per_unit), # Invoice amount matches this GR
                            'BELNR': f"INV{inv_id_counter:05d}",
                            'ACTUAL_DELIVERY_DATE': None
                        })
                        ekbe_count += 1

            self.ekbe_df = pd.DataFrame(ekbe_records)


            save_dataframe(self.ekbe_df, "EKBE.csv", self.config.OUTPUT_DIR, self.config.OUTPUT_FORMAT)
            print(f"Generated {len(self.ekbe_df)} EKBE records.")

        except Exception as e:
            logging.error(f"An error occurred during EKBE data generation: {e}", exc_info=True)
            self.ekbe_df = pd.DataFrame()
    
    def generate_SAP_data(self):
        '''Calls all the individual generator functions'''
        self._calculate_vendor_weights()
        self.generate_lfa1()
        self.generate_mara()
        self.generate_vendor_contract()
        self.generate_ekko()
        self.generate_ekpo()
        self.generate_ekbe()

if __name__ == "__main__":
    #from config import Config
    config=Config()
    generator=SAPDataGenerator(config)
    generator.generate_SAP_data()
    
    


        



    
