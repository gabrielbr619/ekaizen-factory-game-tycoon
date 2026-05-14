import { type ReactNode } from 'react'

type PanelTitleProps = {
  icon: ReactNode
  title: string
}

export function PanelTitle({ icon, title }: PanelTitleProps) {
  return (
    <h2 className="panel-title">
      {icon}
      {title}
    </h2>
  )
}
