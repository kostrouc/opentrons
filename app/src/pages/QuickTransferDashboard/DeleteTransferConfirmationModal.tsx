import * as React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from 'react-query'
import { useTranslation } from 'react-i18next'
import styled from 'styled-components'

import { deleteProtocol, deleteRun, getProtocol } from '@opentrons/api-client'
import {
  ALIGN_CENTER,
  Box,
  COLORS,
  DIRECTION_COLUMN,
  DIRECTION_ROW,
  Flex,
  OVERFLOW_HIDDEN,
  OVERFLOW_WRAP_ANYWHERE,
  SPACING,
  TYPOGRAPHY,
} from '@opentrons/components'
import { useHost, useProtocolQuery } from '@opentrons/react-api-client'

import { SmallButton } from '../../atoms/buttons'
import { OddModal } from '../../molecules/OddModal'
import { useToaster } from '../../organisms/ToasterOven'

import type { OddModalHeaderBaseProps } from '../../molecules/OddModal/types'

interface DeleteTransferConfirmationModalProps {
  transferId: string
  setShowDeleteConfirmationModal: (showDeleteConfirmationModal: boolean) => void
}

export function DeleteTransferConfirmationModal({
  transferId,
  setShowDeleteConfirmationModal,
}: DeleteTransferConfirmationModalProps): JSX.Element {
  const { i18n, t } = useTranslation(['quick_transfer', 'shared'])
  const navigate = useNavigate()
  const { makeSnackbar } = useToaster()
  const [showIcon, setShowIcon] = React.useState<boolean>(false)
  const modalHeader: OddModalHeaderBaseProps = {
    title: t('delete_this_transfer'),
    iconName: 'ot-alert',
    iconColor: COLORS.yellow50,
  }
  const host = useHost()
  const queryClient = useQueryClient()
  const { data: protocolRecord } = useProtocolQuery(transferId)
  const transferName =
    protocolRecord?.data.metadata.protocolName ??
    protocolRecord?.data.files[0].name

  const handleCloseModal = (): void => {
    setShowDeleteConfirmationModal(false)
  }
  const handleDeleteTransfer = (): void => {
    if (host != null && transferId != null) {
      setShowIcon(true)
      getProtocol(host, transferId)
        .then(
          response =>
            response.data.links?.referencingRuns.map(({ id }) => id) ?? []
        )
        .then(referencingRunIds => {
          return Promise.all(
            referencingRunIds?.map(runId => deleteRun(host, runId))
          )
        })
        .then(() => deleteProtocol(host, transferId))
        .then(() =>
          queryClient
            .invalidateQueries([host, 'protocols'])
            .catch((e: Error) => {
              console.error(`error invalidating runs query: ${e.message}`)
            })
        )
        .then(() => {
          setShowIcon(false)
          setShowDeleteConfirmationModal(false)
          navigate('/quick-transfer')
          makeSnackbar(t('deleted_transfer') as string)
        })
        .catch((e: Error) => {
          navigate('/quick-transfer')
          console.error(`error deleting resources: ${e.message}`)
        })
    } else {
      console.error(
        'could not delete resources because the robot host is unknown'
      )
    }
  }
  return (
    <OddModal header={modalHeader}>
      <Flex
        flexDirection={DIRECTION_COLUMN}
        gridGap={SPACING.spacing32}
        width="100%"
      >
        <Box width="100%">
          <TransferNameText>{transferName}</TransferNameText>
          <AdditionalText>{t('will_be_deleted')}</AdditionalText>
        </Box>
        <Flex
          flexDirection={DIRECTION_ROW}
          gridGap={SPACING.spacing8}
          alignItems={ALIGN_CENTER}
        >
          <SmallButton
            flex="1"
            buttonText={i18n.format(t('shared:cancel'), 'capitalize')}
            onClick={handleCloseModal}
          />
          <SmallButton
            flex="1"
            buttonType="alert"
            buttonText={t('shared:delete')}
            onClick={handleDeleteTransfer}
            iconPlacement={showIcon ? 'startIcon' : undefined}
            iconName={showIcon ? 'ot-spinner' : undefined}
          />
        </Flex>
      </Flex>
    </OddModal>
  )
}

const TransferNameText = styled.span`
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: ${OVERFLOW_HIDDEN};
  overflow-wrap: ${OVERFLOW_WRAP_ANYWHERE};
  font-weight: ${TYPOGRAPHY.fontWeightBold};
  font-size: ${TYPOGRAPHY.fontSize22};
  line-height: ${TYPOGRAPHY.lineHeight28};
  color: ${COLORS.grey60};
`
const AdditionalText = styled.span`
  font-weight: ${TYPOGRAPHY.fontWeightRegular};
  font-size: ${TYPOGRAPHY.fontSize22};
  line-height: ${TYPOGRAPHY.lineHeight28};
  color: ${COLORS.grey60};
`
