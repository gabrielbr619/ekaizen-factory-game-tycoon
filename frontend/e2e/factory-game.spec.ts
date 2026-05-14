import { expect, test } from '@playwright/test'

test('plays a complete factory management flow', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'eKaizen Factory Game Tycoon' })).toBeVisible()
  await expect(page.getByLabel('Kanban')).toContainText('Backlog')
  await expect(page.getByText('backend e a fonte autoritativa')).toBeVisible()

  await page.getByRole('button', { name: /Mover/ }).first().click()
  await expect(page.getByText(/enviado para Analise/)).toBeVisible()
  await page.getByLabel('Analise').locator('.card-select').first().click()
  await expect(page.getByRole('button', { name: /Alocar/ }).first()).toBeEnabled()
  await page.getByRole('button', { name: /Alocar/ }).first().click()

  for (let sprint = 0; sprint < 5; sprint += 1) {
    await page.getByRole('button', { name: /Encerrar sprint/ }).click()
    await page.getByRole('button', { name: /Confirmar sprint/ }).click()
    await expect(page.getByText('Sprint processada.')).toBeVisible()
  }

  await page.getByLabel('Contratacoes').getByRole('button').first().click()
  await expect(page.getByText(/contratado/i)).toBeVisible()

  await page.getByRole('button', { name: 'Descanso' }).click()
  await expect(page.getByText(/PDCA aplicado/i)).toBeVisible()

  await page.getByRole('button', { name: 'Hall of Kaizen' }).click()
  await expect(page.getByRole('heading', { name: 'Hall of Kaizen' })).toBeVisible()
  await expect(page.getByText(/Veredito:/)).toBeVisible()
  await expect(page.getByText('Top Kaizens')).toBeVisible()
})
