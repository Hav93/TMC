import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { api, handleApiError } from '../api'

// Mock axios
vi.mock('axios')

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('api.get', () => {
    it('should make GET request and return data', async () => {
      const mockData = { id: 1, name: 'Test' }
      const axiosGetSpy = vi.spyOn(axios, 'get').mockResolvedValue({ data: mockData })

      const result = await api.get('/test')

      expect(axiosGetSpy).toHaveBeenCalledWith('/test', undefined)
      expect(result).toEqual(mockData)
    })
  })

  describe('api.post', () => {
    it('should make POST request with data', async () => {
      const mockData = { id: 1 }
      const postData = { name: 'Test' }
      const axiosPostSpy = vi.spyOn(axios, 'post').mockResolvedValue({ data: mockData })

      const result = await api.post('/test', postData)

      expect(axiosPostSpy).toHaveBeenCalledWith('/test', postData, undefined)
      expect(result).toEqual(mockData)
    })
  })

  describe('handleApiError', () => {
    it('should handle Axios error with response', () => {
      const error = {
        isAxiosError: true,
        response: {
          data: {
            message: 'Test error'
          }
        }
      }

      expect(() => handleApiError(error)).toThrow('Test error')
    })

    it('should handle unknown error', () => {
      const error = new Error('Unknown error')

      expect(() => handleApiError(error)).toThrow('未知错误')
    })
  })
})

