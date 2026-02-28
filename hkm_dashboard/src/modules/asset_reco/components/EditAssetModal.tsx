// Edit Asset Modal Component
import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  HStack,
  Text,
  Select,
  NumberInput,
  NumberInputField,
  useToast,
} from '@chakra-ui/react';
import type { AssetRecoItem } from '../types';
import { SearchableSelect, type SelectOption } from './SearchableSelect';

interface EditAssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  asset: AssetRecoItem | null;
  onSave: (assetName: string, updates: Record<string, any>) => Promise<void>;
  users: SelectOption[];
  onUserSearch: (searchTerm: string) => void;
  loadingUsers: boolean;
}

export const EditAssetModal: React.FC<EditAssetModalProps> = ({
  isOpen,
  onClose,
  asset,
  onSave,
  users,
  onUserSearch,
  loadingUsers,
}) => {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  // Initialize form data when asset changes
  useEffect(() => {
    if (asset) {
      setFormData({
        location: asset.location || '',
        purchased_date: asset.purchased_date || '',
        purchased_amount: asset.purchased_amount || 0,
        secondary_custodian: asset.secondary_custodian || '',
        remarks: asset.remarks || '',
      });
    }
  }, [asset]);

  const handleFieldChange = (fieldname: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [fieldname]: value,
    }));
  };

  const handleSave = async () => {
    if (!asset) return;

    try {
      setSaving(true);
      
      // Only send changed fields
      const updates: Record<string, any> = {};
      Object.keys(formData).forEach((key) => {
        if (formData[key] !== (asset as any)[key]) {
          updates[key] = formData[key];
        }
      });

      if (Object.keys(updates).length === 0) {
        toast({
          title: 'No changes',
          description: 'No fields were modified',
          status: 'info',
          duration: 3000,
          isClosable: true,
        });
        onClose();
        return;
      }

      await onSave(asset.name, updates);
      
      toast({
        title: 'Success',
        description: 'Asset updated successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      onClose();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update asset',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setSaving(false);
    }
  };

  if (!asset) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay bg="blackAlpha.600" backdropFilter="blur(5px)" />
      <ModalContent maxW="600px">
        <ModalHeader bg="blue.500" color="white" borderTopRadius="md">
          <VStack align="start" spacing={1}>
            <Text fontSize="lg" fontWeight="bold">Edit Asset</Text>
            <Text fontSize="sm" fontWeight="normal" opacity={0.9}>
              {asset.name} - {asset.asset_category}
            </Text>
          </VStack>
        </ModalHeader>
        <ModalCloseButton color="white" />
        
        <ModalBody py={6}>
          <VStack spacing={4} align="stretch">
            {/* Location */}
            <FormControl>
              <FormLabel fontSize="sm" fontWeight="semibold" mb={2}>
                Location
              </FormLabel>
              <Input
                value={formData.location || ''}
                onChange={(e) => handleFieldChange('location', e.target.value)}
                placeholder="Enter location"
                size="md"
              />
            </FormControl>

            {/* Date and Amount */}
            <HStack spacing={4}>
              <FormControl flex={1}>
                <FormLabel fontSize="sm" fontWeight="semibold" mb={2}>
                  Purchased Date
                </FormLabel>
                <Input
                  type="date"
                  value={formData.purchased_date || ''}
                  onChange={(e) => handleFieldChange('purchased_date', e.target.value)}
                  size="md"
                />
              </FormControl>

              <FormControl flex={1}>
                <FormLabel fontSize="sm" fontWeight="semibold" mb={2}>
                  Purchased Amount
                </FormLabel>
                <NumberInput
                  value={formData.purchased_amount || 0}
                  onChange={(_, value) => handleFieldChange('purchased_amount', value)}
                  min={0}
                  precision={2}
                  size="md"
                >
                  <NumberInputField />
                </NumberInput>
              </FormControl>
            </HStack>

            {/* Secondary Custodian */}
            <FormControl>
              <FormLabel fontSize="sm" fontWeight="semibold" mb={2}>
                Secondary Custodian
              </FormLabel>
              <SearchableSelect
                size="md"
                options={users}
                value={formData.secondary_custodian || ''}
                onChange={(value) => handleFieldChange('secondary_custodian', value)}
                placeholder="Select user..."
                onSearch={onUserSearch}
                isLoading={loadingUsers}
              />
            </FormControl>

            {/* Remarks */}
            <FormControl>
              <FormLabel fontSize="sm" fontWeight="semibold" mb={2}>
                Remarks
              </FormLabel>
              <Input
                value={formData.remarks || ''}
                onChange={(e) => handleFieldChange('remarks', e.target.value)}
                placeholder="Add remarks..."
                size="md"
              />
            </FormControl>
          </VStack>
        </ModalBody>

        <ModalFooter bg="gray.50" borderBottomRadius="md">
          <HStack spacing={3}>
            <Button variant="ghost" onClick={onClose} isDisabled={saving}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSave}
              isLoading={saving}
              loadingText="Saving..."
            >
              Save Changes
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

