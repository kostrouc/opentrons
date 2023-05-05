import * as React from 'react'
import { renderWithProviders } from '@opentrons/components'

import { NetworkSettings } from '..'
import { i18n } from '../../../../../i18n'
import { getLocalRobot } from '../../../../../redux/discovery'
import type { DiscoveredRobot } from '../../../../../redux/discovery/types'
import { getWifiList } from '../../../../../redux/networking'
import type { WifiNetwork } from '../../../../../redux/networking/types'
import { EthernetConnectionDetails } from '../EthernetConnectionDetails'
import { WifiConnectionDetails } from '../WifiConnectionDetails'

jest.mock('../../../../../redux/discovery')
jest.mock('../../../../../redux/networking')
jest.mock('../WifiConnectionDetails')
jest.mock('../EthernetConnectionDetails')

const mockGetLocalRobot = getLocalRobot as jest.MockedFunction<
  typeof getLocalRobot
>
const mockGetWifiList = getWifiList as jest.MockedFunction<typeof getWifiList>
const mockWifiSettings = WifiConnectionDetails as jest.MockedFunction<
  typeof WifiConnectionDetails
>
const mockEthernetConnectionDetails = EthernetConnectionDetails as jest.MockedFunction<
  typeof EthernetConnectionDetails
>
const mockSetCurrentOption = jest.fn()

const render = (props: React.ComponentProps<typeof NetworkSettings>) => {
  return renderWithProviders(<NetworkSettings {...props} />, {
    i18nInstance: i18n,
  })
}

describe('NetworkSettings', () => {
  let props: React.ComponentProps<typeof NetworkSettings>

  beforeEach(() => {
    props = {
      setCurrentOption: mockSetCurrentOption,
      networkConnection: {
        isWifiConnected: true,
        isEthernetConnected: false,
        isUsbConnected: false,
        connectionStatus: 'Connected via Wi-Fi',
        activeSsid: 'Mock WiFi Network',
      },
    }
    mockGetLocalRobot.mockReturnValue({
      name: 'Otie',
    } as DiscoveredRobot)
    mockGetWifiList.mockReturnValue([
      {
        ssid: 'Mock WiFi Network',
        active: true,
        securityType: 'wpa-psk',
      } as WifiNetwork,
    ])
    mockWifiSettings.mockReturnValue(<div>mock WifiConnectionDetails</div>)
    mockEthernetConnectionDetails.mockReturnValue(
      <div>mock EthernetConnectionDetails</div>
    )
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('displays the wifi, ethernet, and usb network options', () => {
    const [{ getByText }] = render(props)
    expect(getByText('Wi-Fi')).toBeTruthy()
    expect(getByText('Ethernet')).toBeTruthy()
    expect(getByText('USB')).toBeTruthy()
  })

  it('selecting the Wi-Fi option displays the wifi details', () => {
    const [{ getByText }] = render(props)
    getByText('Wi-Fi').click()
    expect(getByText('mock WifiConnectionDetails')).toBeTruthy()
  })

  it('clicking back on the wifi details screen shows the network settings page again', () => {
    const [{ getByText, queryByText, container }] = render(props)
    getByText('Wi-Fi').click()
    container.querySelector('button')?.click()
    expect(queryByText('WIFI DETAILS')).toBeFalsy()
    expect(getByText('Network Settings')).toBeTruthy()
  })

  it('selecting the Ethernet option displays the ethernet details', () => {
    const [{ getByText }] = render(props)
    getByText('Ethernet').click()
    expect(getByText('mock EthernetConnectionDetails')).toBeTruthy()
  })

  it('clicking back on the ethernet details screen shows the network settings page again', () => {
    const [{ getByText, queryByText, container }] = render(props)
    getByText('Ethernet').click()
    container.querySelector('button')?.click()
    expect(queryByText('ETHERNET DETAILS')).toBeFalsy()
    expect(getByText('Network Settings')).toBeTruthy()
  })

  it.todo('selecting the USB option displays the usb details')

  it.todo(
    'clicking back on the usb details screen shows the network settings page again'
  )
})
