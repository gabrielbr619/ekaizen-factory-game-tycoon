import { type Card, type Column, type Developer, type KaizenType } from '../types'

export function nextColumn(column: Column): Column | null {
  if (column === 'backlog') return 'analysis'
  if (column === 'analysis') return 'development'
  if (column === 'development') return 'qa'
  if (column === 'qa') return 'done'
  return null
}

export function columnLabel(column: Column): string {
  if (column === 'backlog') return 'Backlog'
  if (column === 'analysis') return 'Analise'
  if (column === 'development') return 'Dev'
  if (column === 'qa') return 'QA'
  return 'Done'
}

export function columnHelp(column: Column): string {
  if (column === 'backlog') return 'Demanda aguardando pull'
  if (column === 'analysis') return 'PO destrava requisitos'
  if (column === 'development') return 'Execucao tecnica'
  if (column === 'qa') return 'Qualidade e Jidoka'
  return 'Receita entregue'
}

export function cycleSummary(card: Card): string {
  const entries = Object.entries(card.cycle_times)
  if (entries.length === 0) return '0 sp'
  return entries.map(([column, value]) => `${column}:${value}`).join(' ')
}

export function kaizenLabel(kaizen: KaizenType): string {
  if (kaizen === 'train-dev') return 'Treinar Dev'
  if (kaizen === 'poka-yoke') return 'Poka-Yoke'
  if (kaizen === 'qa-automation') return 'QA Auto'
  if (kaizen === 'rest-space') return 'Descanso'
  if (kaizen === 'wip-increase') return 'Aumentar WIP'
  if (kaizen === 'mentoring') return 'Mentoria'
  if (kaizen === 'interns') return 'Estagiarios'
  if (kaizen === 'marketing') return 'Marketing'
  if (kaizen === 'devops-culture') return 'Cultura DevOps'
  return 'Heijunka'
}

export function specialtyBadge(specialty: string): string {
  if (specialty === 'backend') return 'BE'
  if (specialty === 'frontend') return 'FE'
  if (specialty === 'qa') return 'QA'
  if (specialty === 'po') return 'PO'
  if (specialty === 'devops') return 'DO'
  if (specialty === 'fullstack') return 'FS'
  return specialty.slice(0, 2).toUpperCase()
}

export function specialtyLabel(specialty: string): string {
  if (specialty === 'backend') return 'Backend'
  if (specialty === 'frontend') return 'Frontend'
  if (specialty === 'qa') return 'QA'
  if (specialty === 'po') return 'Produto'
  if (specialty === 'devops') return 'DevOps'
  if (specialty === 'fullstack') return 'Fullstack'
  return specialty
}

export function levelLabel(level: string): string {
  if (level === 'junior') return 'Junior'
  if (level === 'pleno') return 'Pleno'
  if (level === 'senior') return 'Senior'
  if (level === 'god-tier') return 'God-tier'
  return level
}

export function allocationTitle(dev: Developer, selectedCard: Card | null, assignedToSelectedCard: boolean): string {
  if (!dev.active) return `${dev.name} esta inativo.`
  if (assignedToSelectedCard) return `Remover ${dev.name} do card selecionado. O backend desaloca com card_id nulo.`
  if (selectedCard === null) return 'Selecione um card antes de alocar.'
  if (selectedCard.column === 'backlog' || selectedCard.column === 'done') {
    return 'Backend so permite alocar em Analise, Dev ou QA.'
  }
  return `Alocar ${dev.name} no card ${selectedCard.title}. O backend valida especialidade e regras ativas.`
}

export function kaizenTarget(kaizen: KaizenType, selectedDev: Developer | null, selectedCard: Card | null): string | null {
  if (kaizen === 'train-dev') return selectedDev?.id ?? null
  if (kaizen === 'wip-increase') return selectedCard?.column ?? 'development'
  return null
}

export function kaizenTargetLabel(kaizen: KaizenType, selectedDev: Developer | null, selectedCard: Card | null): string {
  if (kaizen === 'train-dev') return selectedDev?.name ?? 'selecione um dev'
  if (kaizen === 'wip-increase') return selectedCard === null ? 'Desenvolvimento' : columnLabel(selectedCard.column)
  return 'global'
}

export function verdictLabel(verdict: string): string {
  if (verdict === 'master-kaizen') return 'Mestre Kaizen'
  if (verdict === 'survived') return 'Sobreviveu'
  if (verdict === 'bankrupt') return 'Falencia'
  return 'Em andamento'
}
