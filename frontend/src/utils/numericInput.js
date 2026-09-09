export function sanitizeWholeNumberInput(event) {
  const value = event.target.value.replace(/\D/g, '')
  event.target.value = value
  return value
}
