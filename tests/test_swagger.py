from sunholo.agents import config_to_swagger
import yaml


# Test cases for config_to_swagger and generate_swagger functions
def test_config_to_swagger():
    swagger_yaml = config_to_swagger()
    swagger_dict = yaml.safe_load(swagger_yaml)
    
    assert 'swagger' in swagger_dict
    assert swagger_dict['swagger'] == '2.0'
    assert 'info' in swagger_dict
    assert swagger_dict['info']['title'] == 'Sunholo Multivac API - ${_BRANCH_NAME}'
    assert 'paths' in swagger_dict
    #TODO: more tests for specific agents
