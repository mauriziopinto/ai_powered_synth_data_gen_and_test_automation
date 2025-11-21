import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestTEST_1:
    """
    Verify user login with valid credentials
    
    
    """
    
    @pytest.fixture
    def driver(self):
        driver = webdriver.Chrome()
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_test_1(self, driver):
        """Test: Verify user login with valid credentials"""
        
        # TODO: Implement test steps
        pass
