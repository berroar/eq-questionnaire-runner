import FoodPage from "../generated_pages/new_skip_condition_not_set/food-block.page";
import DrinkPage from "../generated_pages/new_skip_condition_not_set/drink-block.page";
import SubmitPage from "../generated_pages/new_skip_condition_not_set/submit.page";

describe("Skip Conditions - Not Set", () => {
  beforeEach("Load the survey", () => {
    browser.openQuestionnaire("test_new_skip_condition_not_set.json");
  });

  it("Given I do not complete the first page, Then I should see the summary page", () => {
    $(FoodPage.submit()).click();
    expect(browser.getUrl()).to.contain(SubmitPage.pageName);
  });

  it("Given I complete the first page, Then I should see the drink page", () => {
    $(FoodPage.bacon()).click();
    $(FoodPage.submit()).click();
    expect(browser.getUrl()).to.contain(DrinkPage.pageName);
  });
});
