import { test as base } from '@playwright/test';
import { ChatPage } from '../pages/ChatPage';

/**
 * Custom fixture: every test that asks for `chat` gets a ChatPage
 * that is already open on the home page.
 */
export const test = base.extend<{ chat: ChatPage }>({
  chat: async ({ page }, use) => {
    const chat = new ChatPage(page);
    await chat.goto();
    await use(chat);
  },
});

export { expect } from '@playwright/test';
