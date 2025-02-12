import QuestionPageOne from "../../../generated_pages/default/number-question-one.page.js";
import QuestionPageTwo from "../../../generated_pages/default/number-question-two.page.js";
import SubmitPage from "../../../generated_pages/default/submit.page.js";
import QuestionPageOneSkip from "../../../generated_pages/default_with_skip/number-question-one.page.js";
import QuestionPageThreeSkip from "../../../generated_pages/default_with_skip/number-question-three.page.js";

describe("Feature: Default Value", () => {
  it('Given I start default schema, When I do not answer a question, Then "no answer provided" is displayed on the Summary page', () => {
    browser.openQuestionnaire("test_default.json");
    $(QuestionPageOne.submit()).click();
    expect(browser.getUrl()).to.contain(QuestionPageTwo.pageName);
    $(QuestionPageTwo.two()).setValue(123);
    $(QuestionPageTwo.submit()).click();
    expect(browser.getUrl()).to.contain(SubmitPage.pageName);
    expect($(SubmitPage.answerOne()).getText()).to.contain("0");
  });

  it("Given I have not answered a question containing a default value, When I return to the question, Then no value should be displayed", () => {
    browser.openQuestionnaire("test_default.json");
    $(QuestionPageOne.submit()).click();
    expect(browser.getUrl()).to.contain(QuestionPageTwo.pageName);
    $(QuestionPageTwo.two()).setValue(123);
    $(QuestionPageTwo.submit()).click();
    expect(browser.getUrl()).to.contain(SubmitPage.pageName);
    $(SubmitPage.previous()).click();
    expect(browser.getUrl()).to.contain(QuestionPageTwo.pageName);
    $(QuestionPageTwo.previous()).click();
    expect(browser.getUrl()).to.contain(QuestionPageOne.pageName);
    expect($(QuestionPageOne.one()).getValue()).to.equal("");
  });

  it("Given I have not answered a question containing a default value, When a skip condition checks for the default value, Then I should skip the next question", () => {
    browser.openQuestionnaire("test_default_with_skip.json");
    $(QuestionPageOneSkip.submit()).click();
    expect(browser.getUrl()).to.contain(QuestionPageThreeSkip.pageName);
    expect($(QuestionPageThreeSkip.questionText()).getText()).to.contain("Question Three");
  });
});
