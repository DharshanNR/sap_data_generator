import pytest
from tests.Config import sampleconfig
from src.data_generator import SAPDataGenerator


@pytest.fixture
def sample_config():
    config=sampleconfig()
    return config

@pytest.fixture
def sample_data(sample_config):
    d=SAPDataGenerator(sample_config)
    d.generate_SAP_data()
    
    return {'LFA1':d.lfa1_df, 'EKKO':d.ekko_df, 'EKPO':d.ekpo_df, 'EKBE':d.ekbe_df,'CONTRACT':d.contract_df,'MARA':d.mara_df}

@pytest.fixture
def function_hook(sample_config):
    d=SAPDataGenerator(sample_config)
    return d