type TooltipProps = {
  describes?: boolean
  id: string
  text: string
}

export function Tooltip({ describes = true, id, text }: TooltipProps) {
  if (!describes) {
    return (
      <span aria-hidden="true" className="tooltip-content">
        {text}
      </span>
    )
  }

  return (
    <>
      <span className="sr-only" id={id}>
        {text}
      </span>
      <span aria-hidden="true" className="tooltip-content">
        {text}
      </span>
    </>
  )
}
