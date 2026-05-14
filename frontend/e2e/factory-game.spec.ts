import { expect, test } from '@playwright/test'

test('plays a complete factory management flow', async ({ page }) => {
  await page.route('**/games', async (route) => {
    if (route.request().method() !== 'POST' || !route.request().url().endsWith('/games')) {
      await route.continue()
      return
    }

    await route.continue({
      postData: JSON.stringify({ seed: 4242 }),
      headers: {
        ...route.request().headers(),
        'content-type': 'application/json',
      },
    })
  })

  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'eKaizen Factory Game Tycoon' })).toBeVisible()
  await expect(page.getByLabel('Kanban')).toContainText('Backlog')
  await expect(page.getByText('backend e a fonte autoritativa')).toBeVisible()

  const backlogCard = page.getByLabel('Backlog').locator('.work-card').first()
  const cardTitle = await backlogCard.locator('strong').textContent()
  if (cardTitle === null) {
    throw new Error('Expected backlog card title to be rendered.')
  }

  await backlogCard.getByRole('button', { name: /Mover/ }).click()
  await expect(page.getByLabel('Analise')).toContainText(cardTitle)
  await page.getByLabel('Analise').getByText(cardTitle).click()
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
