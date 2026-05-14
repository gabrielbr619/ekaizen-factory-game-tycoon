type AccessibleDetailProps = {
  id: string
  text: string
}

export function AccessibleDetail({ id, text }: AccessibleDetailProps) {
  return (
    <>
      <span className="sr-only" id={id}>
        {text}
      </span>
      <span aria-hidden="true" className="detail-popover">
        {text}
      </span>
    </>
  )
}
