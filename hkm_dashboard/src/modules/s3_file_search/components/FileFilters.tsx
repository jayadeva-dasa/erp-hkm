// File Filters Component

import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Input,
  Select,
  Button,
  Text,
  NumberInput,
  NumberInputField,
  FormControl,
  FormLabel,
  Icon,
  Collapse,
} from '@chakra-ui/react';
import { FiFilter, FiX } from 'react-icons/fi';
import type { S3SearchFilters } from '../types';

interface FileFiltersProps {
  filters: S3SearchFilters;
  onFilterChange: (filters: S3SearchFilters) => void;
  onClearFilters: () => void;
  isOpen: boolean;
}

export const FileFilters: React.FC<FileFiltersProps> = ({
  filters,
  onFilterChange,
  onClearFilters,
  isOpen,
}) => {
  const handleChange = (key: keyof S3SearchFilters, value: any) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <Collapse in={isOpen} animateOpacity>
      <Box
        p={4}
        bg="gray.50"
        borderRadius="md"
        border="1px"
        borderColor="gray.200"
      >
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between">
            <HStack>
              <Icon as={FiFilter} />
              <Text fontWeight="bold">Advanced Filters</Text>
            </HStack>
            <Button
              size="sm"
              variant="ghost"
              leftIcon={<FiX />}
              onClick={onClearFilters}
            >
              Clear All
            </Button>
          </HStack>

          <HStack spacing={4}>
            <FormControl>
              <FormLabel fontSize="sm">File Type</FormLabel>
              <Select
                placeholder="All types"
                value={filters.file_type || ''}
                onChange={(e) => handleChange('file_type', e.target.value)}
                size="sm"
              >
                <option value="image">Images</option>
                <option value="pdf">PDF</option>
                <option value="document">Documents</option>
                <option value="spreadsheet">Spreadsheets</option>
                <option value="video">Videos</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Folder Path</FormLabel>
              <Input
                placeholder="e.g., erp.hkmkota.org/25"
                value={filters.folder_path || ''}
                onChange={(e) => handleChange('folder_path', e.target.value)}
                size="sm"
              />
            </FormControl>
          </HStack>

          <HStack spacing={4}>
            <FormControl>
              <FormLabel fontSize="sm">Min Size (MB)</FormLabel>
              <NumberInput
                value={filters.size_min || ''}
                onChange={(_, value) => handleChange('size_min', value)}
                size="sm"
                min={0}
              >
                <NumberInputField placeholder="0" />
              </NumberInput>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Max Size (MB)</FormLabel>
              <NumberInput
                value={filters.size_max || ''}
                onChange={(_, value) => handleChange('size_max', value)}
                size="sm"
                min={0}
              >
                <NumberInputField placeholder="Unlimited" />
              </NumberInput>
            </FormControl>
          </HStack>

          <HStack spacing={4}>
            <FormControl>
              <FormLabel fontSize="sm">Date From</FormLabel>
              <Input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => handleChange('date_from', e.target.value)}
                size="sm"
              />
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Date To</FormLabel>
              <Input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => handleChange('date_to', e.target.value)}
                size="sm"
              />
            </FormControl>
          </HStack>
        </VStack>
      </Box>
    </Collapse>
  );
};

