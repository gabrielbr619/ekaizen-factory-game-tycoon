import { useId, type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Tooltip } from './Tooltip'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'icon' | 'danger'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: ButtonVariant
}

export function Button({ children, className, variant = 'primary', title, type = 'button', ...props }: ButtonProps) {
  const tooltipId = useId()
  const classes = `ui-button ui-button-${variant}${title === undefined ? '' : ' tooltip-host'}${className === undefined ? '' : ` ${className}`}`
  return (
    <button className={classes} type={type} {...props}>
      {children}
      {title === undefined ? null : <Tooltip describes={false} id={tooltipId} text={title} />}
    </button>
  )
}
