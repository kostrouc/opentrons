import * as React from 'react'
import type { Story, Meta } from '@storybook/react'

import { JogControls } from './index'

export default {
  title: 'App/Molecules/JogControls',
  component: JogControls,
} as Meta

const Template: Story<React.ComponentProps<typeof JogControls>> = args => (
  <JogControls {...args} />
)

export const Primary = Template.bind({})
Primary.args = {
  jog: () => {},
  planes: ['horizontal', 'vertical'],
}
