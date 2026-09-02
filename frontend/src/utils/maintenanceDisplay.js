export const maintenanceSortOptions = [
  { value: 'recent', label: 'Most recent' },
  { value: 'oldest', label: 'Least recent' },
  { value: 'cost-high', label: 'Cost: highest first' },
  { value: 'cost-low', label: 'Cost: lowest first' }
]

export function filterAndSortMaintenances(maintenances, search, sort) {
  const query = search.trim().toLowerCase()
  const filtered = query
    ? maintenances.filter(log => searchableLog(log).includes(query))
    : [...maintenances]

  return filtered.sort((left, right) => {
    if (sort === 'cost-high' || sort === 'cost-low') {
      const costComparison = compareCosts(left.cost, right.cost, sort === 'cost-high')
      return costComparison || compareIds(left, right)
    }

    const leftDate = dateValue(left.date_of_service)
    const rightDate = dateValue(right.date_of_service)
    const comparison = sort === 'oldest' ? leftDate - rightDate : rightDate - leftDate
    return comparison || compareIds(left, right)
  })
}

function searchableLog(log) {
  return [
    log.work_done,
    log.service_provider,
    log.notes,
    log.category,
    log.date_of_service,
    log.mileage,
    log.done_by
  ].filter(value => value !== null && value !== undefined).join(' ').toLowerCase()
}

function compareCosts(left, right, descending) {
  const leftKnown = Number.isFinite(left)
  const rightKnown = Number.isFinite(right)
  if (!leftKnown && !rightKnown) return 0
  if (!leftKnown) return 1
  if (!rightKnown) return -1
  return descending ? right - left : left - right
}

function dateValue(value) {
  const parsed = Date.parse(value)
  return Number.isFinite(parsed) ? parsed : 0
}

function compareIds(left, right) {
  return String(left._id ?? '').localeCompare(String(right._id ?? ''))
}
