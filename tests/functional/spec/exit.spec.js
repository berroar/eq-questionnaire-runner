import CensusThankYouPage from "../base_pages/census-thank-you.page.js";
import HubPage from "../base_pages/hub.page";
import { SubmitPage } from "../base_pages/submit.page.js";

describe("Post submission exit", () => {
  beforeEach("Load the survey", () => {
    browser.openQuestionnaire("test_thank_you_census_household.json");
  });

  it("Given I click the exit button from the thank you page which has no session cookie, When I am redirected, Then I should be redirected to the correct log out url", () => {
    $(SubmitPage.submit()).click();
    $(HubPage.submit()).click();
    browser.deleteAllCookies();
    $(CensusThankYouPage.exit()).click();
    expect(browser.getUrl()).to.equal("https://surveys.ons.gov.uk/sign-in/");
  });

  it("Given I click the exit button from the thank you page, When I am redirected, Then I should be redirected to the correct log out url", () => {
    $(SubmitPage.submit()).click();
    $(HubPage.submit()).click();
    $(CensusThankYouPage.exit()).click();
    expect(browser.getUrl()).to.equal("https://census.gov.uk/en/start");
  });

  it("Given I have clicked the exit button, When I navigate back, Then I am taken to the session timed out page", () => {
    $(SubmitPage.submit()).click();
    $(HubPage.submit()).click();
    $(CensusThankYouPage.exit()).click();
    browser.back();
    expect(browser.getUrl()).to.contain("submitted/thank-you");
    expect($("body").getHTML()).to.contain("Sorry, you need to sign in again");
  });
});
