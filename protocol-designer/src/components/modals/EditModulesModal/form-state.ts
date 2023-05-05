import { usePrevious } from '@opentrons/components'
import { useFormikContext } from 'formik'
import { useEffect } from 'react'

import { EditModulesFormValues } from '.'
import { isModuleWithCollisionIssue } from '../../modules/utils'

export const useResetSlotOnModelChange = (
  supportedModuleSlot: string
): void => {
  const { values, setValues } = useFormikContext<EditModulesFormValues>()
  const selectedModel = values.selectedModel
  const prevSelectedModel = usePrevious(selectedModel)
  useEffect(() => {
    if (
      prevSelectedModel &&
      prevSelectedModel !== selectedModel &&
      // @ts-expect-error(sa, 2021-6-22): selectedModel might be null
      isModuleWithCollisionIssue(selectedModel)
    ) {
      setValues({
        selectedModel,
        selectedSlot: supportedModuleSlot,
      })
    }
  })
}
