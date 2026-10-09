import { expect, type Locator, type Page } from '@playwright/test';

// The demo scales to zero, so the first request may wait for a cold start,
// and each answer needs several LLM calls.
const PAGE_TIMEOUT = 120_000;
const ANSWER_TIMEOUT = 120_000;

/**
 * Page Object for the assistant's single page: the chat, the trace panel
 * and the upload panel. Tests use these methods instead of raw selectors,
 * so a change in the HTML is fixed here only.
 */
export class ChatPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly questionInput: Locator;
  readonly askButton: Locator;
  readonly examples: Locator;
  readonly sourceUsed: Locator;
  readonly trace: Locator;
  readonly openUploadButton: Locator;
  readonly fileInput: Locator;
  readonly uploadButton: Locator;
  readonly uploadStatus: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.locator('h1');
    this.questionInput = page.locator('#question');
    this.askButton = page.getByRole('button', { name: 'Ask Agent' });
    this.examples = page.locator('.example');
    this.sourceUsed = page.locator('#sourceUsed');
    this.trace = page.locator('#trace');
    this.openUploadButton = page.locator('#openUpload');
    this.fileInput = page.locator('#fileInput');
    this.uploadButton = page.locator('#uploadBtn');
    this.uploadStatus = page.locator('#uploadStatus');
  }

  async goto(): Promise<void> {
    await this.page.goto('/', { timeout: PAGE_TIMEOUT });
    await expect(this.heading).toContainText('Wealth Banking', { timeout: PAGE_TIMEOUT });
  }

  exampleButton(text: string): Locator {
    return this.page.getByRole('button', { name: text });
  }

  /** Type a question, send it and wait until the agent has finished. */
  async ask(question: string): Promise<void> {
    await this.questionInput.fill(question);
    await this.askButton.click();
    await this.waitForAnswer();
  }

  /** Click one of the example questions and wait for the answer. */
  async askExample(text: string): Promise<void> {
    await this.exampleButton(text).click();
    await this.waitForAnswer();
  }

  /** "Final Source" shows "—" before a question and "Running" while the agent works. */
  async waitForAnswer(): Promise<void> {
    await expect(this.sourceUsed).not.toHaveText(/^(—|Running)$/, { timeout: ANSWER_TIMEOUT });
  }

  /** The most recent answer bubble from the assistant. */
  lastAnswer(): Locator {
    return this.page.locator('.message.assistant .bubble').last();
  }

  /** Open the upload panel and submit a small text file (no admin key entered). */
  async uploadTextFile(fileName: string, content: string): Promise<void> {
    await this.openUploadButton.click();
    await this.fileInput.setInputFiles({
      name: fileName,
      mimeType: 'text/plain',
      buffer: Buffer.from(content, 'utf-8'),
    });
    await this.uploadButton.click();
  }
}
