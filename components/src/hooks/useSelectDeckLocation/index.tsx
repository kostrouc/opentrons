import * as React from 'react'
import isEqual from 'lodash/isEqual'
import { DeckDefinition, getDeckDefFromRobotType } from '@opentrons/shared-data'
import { RobotCoordinateSpace } from '../../hardware-sim/RobotCoordinateSpace'

import type { ModuleLocation, RobotType } from '@opentrons/shared-data'
import { COLORS, SPACING } from '../../ui-style-constants'
import { RobotCoordsForeignDiv, SlotLabels } from '../../hardware-sim'
import { Icon } from '../../icons'
import { Text } from '../../primitives'
import { ALIGN_CENTER, JUSTIFY_CENTER } from '../../styles'
import { DeckSlotLocation } from '../../hardware-sim/DeckSlotLocation'

const X_CROP_MM = 0
const X_ADJUSTMENT_FOR_TC = '-50'
const Y_ADJUSTMENT_FOR_TC = '214'

export function useDeckLocationSelect(
  robotType: RobotType
): { DeckLocationSelect: JSX.Element; selectedLocation: ModuleLocation } {
  const deckDef = getDeckDefFromRobotType(robotType)
  const [
    selectedLocation,
    setSelectedLocation,
  ] = React.useState<ModuleLocation>({
    slotName: deckDef.locations.orderedSlots[0].id,
  })
  return {
    DeckLocationSelect: (
      <DeckLocationSelect
        {...{ deckDef, selectedLocation, setSelectedLocation }}
      />
    ),
    selectedLocation,
  }
}

interface DeckLocationSelectProps {
  deckDef: DeckDefinition
  selectedLocation: ModuleLocation
  setSelectedLocation: (loc: ModuleLocation) => void
  disabledLocations?: ModuleLocation[]
  isThermocycler?: boolean
}
export function DeckLocationSelect({
  deckDef,
  selectedLocation,
  setSelectedLocation,
  disabledLocations = [],
  isThermocycler = false,
}: DeckLocationSelectProps): JSX.Element {
  return (
    <RobotCoordinateSpace
      viewBox={`${deckDef.cornerOffsetFromOrigin[0] + X_CROP_MM} ${
        deckDef.cornerOffsetFromOrigin[1]
      } ${deckDef.dimensions[0] - X_CROP_MM * 2} ${deckDef.dimensions[1]}`}
    >
      {deckDef.locations.orderedSlots.map(slot => {
        const slotLocation = { slotName: slot.id }
        const isDisabled = disabledLocations.some(
          l =>
            typeof l === 'object' && 'slotName' in l && l.slotName === slot.id
        )
        const isSelected = isEqual(selectedLocation, slotLocation)
        let fill = COLORS.highlightPurple2
        if (isSelected) fill = COLORS.highlightPurple1
        if (isDisabled) fill = COLORS.darkGreyDisabled
        if (isSelected && slot.id === 'B1' && isThermocycler) {
          return (
            <g>
              <path
                fill={fill}
                d="M-97.8,496.6h239c2.3,0,4.2-1.9,4.2-4.2v-282c0-2.3-1.9-4.2-4.2-4.2h-239c-2.3,0-4.2,1.9-4.2,4.2v282 C-102,494.7-100.1,496.6-97.8,496.6z"
              />
              <RobotCoordsForeignDiv
                x={X_ADJUSTMENT_FOR_TC}
                y={Y_ADJUSTMENT_FOR_TC}
                width={slot.boundingBox.xDimension}
                height="282"
                innerDivProps={INNER_DIV_PROPS}
              >
                <Icon name="check-circle" size="1.5rem" color={COLORS.white} />
                <Text color={COLORS.white} fontSize="1.5rem">
                  Selected
                </Text>
              </RobotCoordsForeignDiv>
            </g>
          )
        } else if (slot.id === 'A1' && isThermocycler) {
          return null
        }
        console.log(slot.position[1])
        return (
          <React.Fragment key={slot.id}>
            <DeckSlotLocation
              slotName={slot.id}
              slotBaseColor={fill}
              slotClipColor={COLORS.white}
              onClick={() => !isDisabled && setSelectedLocation(slotLocation)}
              cursor={isDisabled || isSelected ? 'default' : 'pointer'}
              deckDefinition={deckDef}
            />
            {isSelected ? (
              <g>
                {/* <path
                  fill={fill}
                  d="M-97.8,496.6h239c2.3,0,4.2-1.9,4.2-4.2v-70c0-2.3-1.9-4.2-4.2-4.2h-239c-2.3,0-4.2,1.9-4.2,4.2v70 C-102,494.7-100.1,496.6-97.8,496.6z"
                /> */}
                <RobotCoordsForeignDiv
                  x={slot.position[0]}
                  y={slot.position[1]}
                  width={slot.boundingBox.xDimension}
                  height={slot.boundingBox.yDimension}
                  innerDivProps={INNER_DIV_PROPS}
                >
                  <Icon
                    name="check-circle"
                    size="1.5rem"
                    color={COLORS.white}
                  />
                  <Text color={COLORS.white} fontSize="1.5rem">
                    Selected
                  </Text>
                </RobotCoordsForeignDiv>
              </g>
            ) : null}
          </React.Fragment>
        )
      })}
      <SlotLabels
        robotType={deckDef.robot.model}
        color={COLORS.darkGreyEnabled}
      />
    </RobotCoordinateSpace>
  )
}

const INNER_DIV_PROPS = {
  display: 'flex',
  alignItems: ALIGN_CENTER,
  justifyContent: JUSTIFY_CENTER,
  height: '100%',
  gridGap: SPACING.spacing4,
}
