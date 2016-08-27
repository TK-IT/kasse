import contextlib
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class MyTest(StaticLiveServerTestCase):
    fixtures = ['user']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.browser = webdriver.Chrome()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    @contextlib.contextmanager
    def wait_for_page_load(self):
        page = self.browser.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.browser, 10).until(EC.staleness_of(page))

    def submit_by_xpath(self, xpath):
        with self.wait_for_page_load():
            self.browser.find_element_by_xpath(xpath).click()

    def test_login(self):
        self.browser.get(self.live_server_url)

        username_input = self.browser.find_element_by_name("username")
        username_input.send_keys('luser')
        password_input = self.browser.find_element_by_name("password")
        password_input.send_keys('hunter2')
        self.submit_by_xpath('//input[@value="Login"]')
        self.assertEquals(self.browser.title, "Lokaleplaner")
        self.submit_by_xpath('//input[@value="Opret ny"]')
