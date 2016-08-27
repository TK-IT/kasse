import contextlib
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
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

        username_input = self.browser.find_element_by_id("profile_text")
        username_input.click()
        username_input.send_keys('bru', Keys.TAB)
        password_input = self.browser.find_element_by_name("password")
        password_input.send_keys('hunter2')
        self.submit_by_xpath('//input[@value="Log ind"]')
        self.assertEquals(self.browser.title, "En kasse i en festforening")

        self.browser.get(self.live_server_url + '/timetrial/stopwatch/')
        profile_input = self.browser.find_element_by_name('profile')
        profile_select = Select(profile_input)
        profile_select.select_by_value('1')
        self.submit_by_xpath('//input[@value="Åbn stopur nu!"]')
        self.assertIn("Stopur", self.browser.title)
