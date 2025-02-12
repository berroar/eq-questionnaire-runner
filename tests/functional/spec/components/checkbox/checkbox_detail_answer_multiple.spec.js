import MandatoryCheckboxPage from "../../../generated_pages/checkbox_detail_answer_multiple/mandatory-checkbox.page";
import SubmitPage from "../../../generated_pages/checkbox_detail_answer_multiple/submit.page";

describe('Checkbox with multiple "detail_answer" options', () => {
  const checkboxSchema = "test_checkbox_detail_answer_multiple.json";

  it("Given detail answer options are available, When the user clicks an option, Then the detail answer input should be visible.", () => {
    browser.openQuestionnaire(checkboxSchema);
    $(MandatoryCheckboxPage.yourChoice()).click();
    expect($(MandatoryCheckboxPage.yourChoiceDetail()).isDisplayed()).to.be.true;
    $(MandatoryCheckboxPage.cheese()).click();
    expect($(MandatoryCheckboxPage.cheeseDetail()).isDisplayed()).to.be.true;
  });

  it("Given a mandatory detail answer, When I select the option but leave the input field empty and submit, Then an error should be displayed.", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    // When
    // Non-Mandatory detail answer given
    $(MandatoryCheckboxPage.cheese()).click();
    $(MandatoryCheckboxPage.cheeseDetail()).setValue("Mozzarella");
    // Mandatory detail answer left blank
    $(MandatoryCheckboxPage.yourChoice()).click();
    $(MandatoryCheckboxPage.submit()).click();
    // Then
    expect($(MandatoryCheckboxPage.error()).isDisplayed()).to.be.true;
    expect($(MandatoryCheckboxPage.errorNumber(1)).getText()).to.contain("Enter your topping choice to continue");
  });

  it("Given a selected checkbox answer with an error for a mandatory detail answer, When I enter valid value and submit the page, Then the error is cleared and I navigate to next page.", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    $(MandatoryCheckboxPage.yourChoice()).click();
    $(MandatoryCheckboxPage.submit()).click();
    expect($(MandatoryCheckboxPage.error()).isDisplayed()).to.be.true;

    // When
    $(MandatoryCheckboxPage.yourChoiceDetail()).setValue("Bacon");
    $(MandatoryCheckboxPage.submit()).click();
    expect(browser.getUrl()).to.contain(SubmitPage.pageName);
  });

  it("Given a non-mandatory detail answer, When the user does not provide any text, Then just the option value should be displayed on the summary screen", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    // When
    $(MandatoryCheckboxPage.cheese()).click();
    expect($(MandatoryCheckboxPage.cheeseDetail()).isDisplayed()).to.be.true;
    $(MandatoryCheckboxPage.submit()).click();
    // Then
    expect($(SubmitPage.mandatoryCheckboxAnswer()).getText()).to.equal("Cheese");
  });

  it("Given multiple detail answers, When the user provides text for all, Then that text should be displayed on the summary screen", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    // When
    $(MandatoryCheckboxPage.cheese()).click();
    $(MandatoryCheckboxPage.cheeseDetail()).setValue("Mozzarella");
    $(MandatoryCheckboxPage.yourChoice()).click();
    $(MandatoryCheckboxPage.yourChoiceDetail()).setValue("Bacon");
    $(MandatoryCheckboxPage.submit()).click();
    // Then
    expect($(SubmitPage.mandatoryCheckboxAnswer()).getText()).to.equal("Cheese\nMozzarella\nYour choice\nBacon");
  });

  it("Given multiple detail answers, When the user provides text for just one, Then that text should be displayed on the summary screen", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    // When
    $(MandatoryCheckboxPage.yourChoice()).click();
    $(MandatoryCheckboxPage.yourChoiceDetail()).setValue("Bacon");
    $(MandatoryCheckboxPage.submit()).click();
    // Then
    expect($(SubmitPage.mandatoryCheckboxAnswer()).getText()).to.equal("Your choice\nBacon");
  });

  it("Given I have previously added text in a detail answer and saved, When I uncheck the detail answer option and select a different checkbox, Then the text entered in the detail answer field should be empty.", () => {
    // Given
    browser.openQuestionnaire(checkboxSchema);
    // When
    $(MandatoryCheckboxPage.cheese()).click();
    $(MandatoryCheckboxPage.cheeseDetail()).setValue("Mozzarella");
    $(MandatoryCheckboxPage.submit()).click();
    $(SubmitPage.previous()).click();
    $(MandatoryCheckboxPage.cheese()).click();
    $(MandatoryCheckboxPage.ham()).click();
    $(MandatoryCheckboxPage.submit()).click();
    $(SubmitPage.previous()).click();
    // Then
    $(MandatoryCheckboxPage.cheese()).click();
    expect($(MandatoryCheckboxPage.cheeseDetail()).getValue()).to.equal("");
  });
});
