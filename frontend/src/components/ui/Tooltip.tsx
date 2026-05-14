import { useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'

type TooltipProps = {
  describes?: boolean
  id: string
  text: string
}

type TooltipPlacement = 'top' | 'bottom'

type TooltipPosition = {
  left: number
  placement: TooltipPlacement
  top: number
  width: number
}

const viewportPadding = 12
const hostGap = 9
const minTooltipWidth = 180
const preferredTooltipWidth = 280
const maxTooltipWidth = 340
const tooltipOpenEvent = 'factory-tooltip-open'

export function Tooltip({ describes = true, id, text }: TooltipProps) {
  const anchorRef = useRef<HTMLSpanElement>(null)
  const tooltipRef = useRef<HTMLSpanElement>(null)
  const hostRef = useRef<HTMLElement | null>(null)
  const reactId = useId()
  const [open, setOpen] = useState(false)
  const [position, setPosition] = useState<TooltipPosition>({
    left: 0,
    placement: 'top',
    top: 0,
    width: preferredTooltipWidth,
  })

  const hideTooltip = () => setOpen(false)

  const updatePosition = () => {
    const host = hostRef.current
    if (host === null) return

    const hostRect = host.getBoundingClientRect()
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight
    const availableWidth = Math.max(120, viewportWidth - viewportPadding * 2)
    const width = Math.min(maxTooltipWidth, Math.max(minTooltipWidth, Math.min(preferredTooltipWidth, availableWidth)))
    const tooltipHeight = tooltipRef.current?.offsetHeight ?? 64
    const spaceAbove = hostRect.top - viewportPadding
    const placement: TooltipPlacement = spaceAbove >= tooltipHeight + hostGap ? 'top' : 'bottom'
    const centeredLeft = hostRect.left + hostRect.width / 2 - width / 2
    const left = Math.min(Math.max(centeredLeft, viewportPadding), viewportWidth - viewportPadding - width)
    const top =
      placement === 'top'
        ? Math.max(viewportPadding, hostRect.top - tooltipHeight - hostGap)
        : Math.min(viewportHeight - viewportPadding - tooltipHeight, hostRect.bottom + hostGap)

    setPosition({ left, placement, top, width })
  }

  useEffect(() => {
    const host = hostRef.current
    if (host === undefined || host === null) return undefined

    const showTooltip = () => {
      document.dispatchEvent(new CustomEvent(tooltipOpenEvent, { detail: reactId }))
      updatePosition()
      setOpen(true)
    }

    const handleFocusOut = (event: FocusEvent) => {
      if (event.relatedTarget instanceof Node && host.contains(event.relatedTarget)) return
      hideTooltip()
    }

    host.addEventListener('pointerenter', showTooltip)
    host.addEventListener('pointermove', updatePosition)
    host.addEventListener('pointerleave', hideTooltip)
    host.addEventListener('focusin', showTooltip)
    host.addEventListener('focusout', handleFocusOut)
    host.addEventListener('click', hideTooltip)
    host.addEventListener('pointerdown', hideTooltip)

    return () => {
      host.removeEventListener('pointerenter', showTooltip)
      host.removeEventListener('pointermove', updatePosition)
      host.removeEventListener('pointerleave', hideTooltip)
      host.removeEventListener('focusin', showTooltip)
      host.removeEventListener('focusout', handleFocusOut)
      host.removeEventListener('click', hideTooltip)
      host.removeEventListener('pointerdown', hideTooltip)
    }
  }, [reactId, text])

  useEffect(() => {
    const handleAnotherTooltipOpen = (event: Event) => {
      if (event instanceof CustomEvent && event.detail !== reactId) hideTooltip()
    }

    document.addEventListener(tooltipOpenEvent, handleAnotherTooltipOpen)

    return () => {
      document.removeEventListener(tooltipOpenEvent, handleAnotherTooltipOpen)
    }
  }, [reactId])

  useEffect(() => {
    if (!open) return undefined

    const handleDocumentEvent = (event: Event) => {
      const host = hostRef.current
      if (event.type === 'keydown' && event instanceof KeyboardEvent && event.key !== 'Escape') return
      if (event.type === 'pointerdown' && event.target instanceof Node && host?.contains(event.target)) return
      hideTooltip()
    }

    const handleViewportChange = () => updatePosition()

    document.addEventListener('keydown', handleDocumentEvent)
    document.addEventListener('pointerdown', handleDocumentEvent)
    window.addEventListener('resize', handleViewportChange)
    window.addEventListener('scroll', handleViewportChange, true)

    return () => {
      document.removeEventListener('keydown', handleDocumentEvent)
      document.removeEventListener('pointerdown', handleDocumentEvent)
      window.removeEventListener('resize', handleViewportChange)
      window.removeEventListener('scroll', handleViewportChange, true)
    }
  }, [open, text])

  useLayoutEffect(() => {
    hostRef.current = anchorRef.current?.parentElement ?? null
  }, [])

  useLayoutEffect(() => {
    if (open) updatePosition()
  }, [open, text])

  const visualTooltip = createPortal(
    <span
      aria-hidden="true"
      className="tooltip-content"
      data-open={open ? 'true' : 'false'}
      data-placement={position.placement}
      id={`${reactId}-visual`}
      ref={tooltipRef}
      style={{
        left: `${position.left}px`,
        top: `${position.top}px`,
        width: `${position.width}px`,
      }}
    >
      {text}
    </span>,
    document.body,
  )

  return (
    <>
      <span aria-hidden="true" className="tooltip-anchor" ref={anchorRef} />
      {describes ? (
        <span className="sr-only" id={id}>
          {text}
        </span>
      ) : null}
      {visualTooltip}
    </>
  )
}
