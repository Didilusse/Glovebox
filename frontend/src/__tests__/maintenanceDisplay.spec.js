import { describe, expect, it } from 'vitest'

import { filterAndSortMaintenances } from '../utils/maintenanceDisplay.js'


const logs = [
  {
    _id: 'b', date_of_service: '2024-01-15', cost: 80, mileage: 72000,
    work_done: 'Oil change', service_provider: 'Valvoline', notes: 'Synthetic oil', category: 'fluids', done_by: 'shop'
  },
  {
    _id: 'a', date_of_service: '2025-04-11', cost: null, mileage: null,
    work_done: 'A/C refrigerant recharged', service_provider: "Ronnie's Total Car Care", notes: 'Imported from CARFAX', category: 'other', done_by: 'shop'
  },
  {
    _id: 'c', date_of_service: '2023-10-24', cost: 450, mileage: 94986,
    work_done: 'Alternator replaced', service_provider: 'Honda', notes: 'Electrical repair', category: 'engine', done_by: 'self'
  }
]


describe('filterAndSortMaintenances', () => {
  it('searches every useful maintenance field without case sensitivity', () => {
    expect(filterAndSortMaintenances(logs, 'vALvoLine', 'recent').map(log => log._id)).toEqual(['b'])
    expect(filterAndSortMaintenances(logs, 'synthetic', 'recent').map(log => log._id)).toEqual(['b'])
    expect(filterAndSortMaintenances(logs, '94986', 'recent').map(log => log._id)).toEqual(['c'])
    expect(filterAndSortMaintenances(logs, '2025-04', 'recent').map(log => log._id)).toEqual(['a'])
    expect(filterAndSortMaintenances(logs, 'self', 'recent').map(log => log._id)).toEqual(['c'])
    expect(filterAndSortMaintenances(logs, 'engine', 'recent').map(log => log._id)).toEqual(['c'])
  })

  it('orders dates from most recent and least recent', () => {
    expect(filterAndSortMaintenances(logs, '', 'recent').map(log => log._id)).toEqual(['a', 'b', 'c'])
    expect(filterAndSortMaintenances(logs, '', 'oldest').map(log => log._id)).toEqual(['c', 'b', 'a'])
  })

  it('orders known costs while always placing unknown costs last', () => {
    expect(filterAndSortMaintenances(logs, '', 'cost-high').map(log => log._id)).toEqual(['c', 'b', 'a'])
    expect(filterAndSortMaintenances(logs, '', 'cost-low').map(log => log._id)).toEqual(['b', 'c', 'a'])
  })

  it('filters by service category alongside search', () => {
    expect(filterAndSortMaintenances(logs, '', 'recent', 'engine').map(log => log._id)).toEqual(['c'])
    expect(filterAndSortMaintenances(logs, 'oil', 'recent', 'fluids').map(log => log._id)).toEqual(['b'])
    expect(filterAndSortMaintenances(logs, 'oil', 'recent', 'engine')).toEqual([])
  })

  it('uses record ID as a stable tie-breaker and never mutates the source', () => {
    const equalDate = [{ ...logs[0], _id: 'z' }, { ...logs[0], _id: 'a' }]
    const original = [...equalDate]
    expect(filterAndSortMaintenances(equalDate, '', 'recent').map(log => log._id)).toEqual(['a', 'z'])
    expect(equalDate).toEqual(original)
  })
})
