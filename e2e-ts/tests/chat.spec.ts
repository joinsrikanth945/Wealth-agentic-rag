import { test, expect } from './fixtures';

// End-to-end tests through a real browser, against E2E_BASE_URL
// (the live Azure deployment in CI, or http://127.0.0.1:8080 locally).
// The question tests use the real LLM: a full run costs about 1-2 cents.

const TOKEN_QUESTION = 'How do I register a LumenKey token?';

test.describe('Home page', () => {
  test('shows the heading and the example questions @smoke', async ({ chat }) => {
    await expect(chat.examples).toHaveCount(3);
    await expect(chat.exampleButton(TOKEN_QUESTION)).toBeVisible();
    await expect(chat.sourceUsed).toHaveText('—');
  });
});

test.describe('Answer paths', () => {
  test('example question is answered from the documents, with citation and trace', async ({ chat }) => {
    await chat.askExample(TOKEN_QUESTION);

    await expect(chat.sourceUsed).toHaveText('private_kb');
    await expect(chat.lastAnswer()).toContainText(/QR/i);
    await expect(chat.lastAnswer().locator('.citations')).toContainText('secure_access_token_guide');
    await expect(chat.trace).toContainText('PRIVATE KB');
  });

  test('greeting is answered directly, without retrieval', async ({ chat }) => {
    await chat.ask('Hello, good morning!');

    await expect(chat.sourceUsed).toHaveText('direct');
    await expect(chat.trace).toContainText('Direct response');
    await expect(chat.trace).not.toContainText('retrieval →');
  });

  test('trap question is not answered with an invented fee @regression', async ({ chat }) => {
    // Regression test for issue #1: the general custody fee (0.25%)
    // must not be applied to crypto assets.
    await chat.ask("What is LumenWealth's custody fee for crypto assets?");

    await expect(chat.sourceUsed).toHaveText(/^(insufficient_evidence|web_search)$/);
    await expect(chat.lastAnswer()).not.toContainText('0.25%');
  });
});

test.describe('Upload security', () => {
  test('upload without the admin key is refused @smoke', async ({ chat }) => {
    await chat.uploadTextFile('note.txt', 'End-to-end test upload.');

    await expect(chat.uploadStatus).toContainText('Invalid admin key', { timeout: 120_000 });
  });
});
