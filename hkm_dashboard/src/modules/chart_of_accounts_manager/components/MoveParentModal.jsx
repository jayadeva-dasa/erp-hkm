import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Button,
  VStack,
  Text,
  useToast,
  List,
  ListItem,
  Box,
} from '@chakra-ui/react';
import { updateAccountParent, validateAccountMove } from '../api/chartOfAccountsApi';
import { getAccountTypeColor } from '../utils/accountUtils';

const MoveParentModal = ({
  isOpen,
  onClose,
  account,
  groupAccounts,
  company,
  onSuccess,
}) => {
  const [selectedParent, setSelectedParent] = useState(null);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const handleMove = async () => {
    if (!selectedParent || !account) return;
    setLoading(true);
    try {
      const validation = await validateAccountMove(account.name, selectedParent.name);
      if (!validation.valid) {
        toast({ title: 'Invalid move', description: validation.message, status: 'warning', duration: 4000, isClosable: true });
        setLoading(false);
        return;
      }
      await updateAccountParent(account.name, selectedParent.name, company);
      toast({ title: 'Moved', description: `Now under "${selectedParent.account_name}"`, status: 'success', duration: 2000, isClosable: true });
      onSuccess(selectedParent.name);
      onClose();
    } catch (err) {
      toast({ title: 'Error', description: err.message || 'Failed to move', status: 'error', duration: 4000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  const color = getAccountTypeColor(account?.root_type);

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="sm">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader fontSize="sm">Change parent</ModalHeader>
        <ModalCloseButton size="sm" />
        <ModalBody pt={0}>
          <Text fontSize="xs" color="gray.500" mb={2}>
            Move &quot;{account?.account_name}&quot; under:
          </Text>
          <List spacing={0} maxH="280px" overflowY="auto">
            {groupAccounts.map((parent) => (
              <ListItem key={parent.name}>
                <Box
                  as="button"
                  w="100%"
                  textAlign="left"
                  py={1.5}
                  px={2}
                  fontSize="sm"
                  borderRadius="md"
                  borderLeftWidth="3px"
                  borderLeftColor={selectedParent?.name === parent.name ? `${color}.500` : 'transparent'}
                  bg={selectedParent?.name === parent.name ? `${color}.50` : 'transparent'}
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => setSelectedParent(parent)}
                >
                  {parent.account_name}
                </Box>
              </ListItem>
            ))}
          </List>
          {groupAccounts.length === 0 && (
            <Text fontSize="xs" color="gray.500">No other group accounts of this type.</Text>
          )}
        </ModalBody>
        <ModalFooter>
          <Button size="sm" variant="ghost" onClick={onClose}>Cancel</Button>
          <Button size="sm" colorScheme={color} onClick={handleMove} isDisabled={!selectedParent} isLoading={loading}>
            Move
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default MoveParentModal;
