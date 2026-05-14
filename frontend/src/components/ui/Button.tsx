import { type ButtonHTMLAttributes, type ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'icon' | 'danger'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  variant?: ButtonVariant
}

export function Button({ children, className, variant = 'primary', type = 'button', ...props }: ButtonProps) {
  const classes = `ui-button ui-button-${variant}${className === undefined ? '' : ` ${className}`}`
  return (
    <button className={classes} type={type} {...props}>
      {children}
    </button>
  )
}
