// Searchable Single-Select Component for Asset Reco
import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Box,
  Input,
  InputGroup,
  InputLeftElement,
  VStack,
  Text,
  Icon,
  HStack,
  useDisclosure,
  Spinner,
  InputRightElement,
} from '@chakra-ui/react';
import { SearchIcon, ChevronDownIcon } from '@chakra-ui/icons';

export interface SelectOption {
  value: string;
  label: string;
}

interface SearchableSelectProps {
  options: SelectOption[];
  value: string;
  onChange: (selected: string) => void;
  placeholder?: string;
  onSearch?: (searchTerm: string) => void;
  isLoading?: boolean;
  isDisabled?: boolean;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  emptyMessage?: string;
}

export const SearchableSelect: React.FC<SearchableSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  onSearch,
  isLoading = false,
  isDisabled = false,
  size = 'xs',
  emptyMessage = 'No results found',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const prevOptionsLengthRef = useRef<number>(options.length);

  // Handle click outside to close dropdown and handle scroll
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        handleClose();
      }
    };

    const handleScroll = (event: Event) => {
      if (!isOpen) return;
      
      // Check if scroll is happening inside the dropdown's scrollable container
      const target = event.target as HTMLElement;
      
      // If scroll is on the dropdown's scrollable container, don't close
      if (scrollContainerRef.current && (target === scrollContainerRef.current || scrollContainerRef.current.contains(target))) {
        return;
      }
      
      // If scroll is anywhere inside the dropdown, don't close
      if (dropdownRef.current && target && dropdownRef.current.contains(target)) {
        return;
      }
      
      // Page scroll outside dropdown, close it
      handleClose();
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      // Listen to scroll events on window, but check if they're from inside dropdown
      window.addEventListener('scroll', handleScroll, true);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('scroll', handleScroll, true);
    };
  }, [isOpen]);

  // When options change (backend results arrive), maintain focus on input
  useEffect(() => {
    if (isOpen && inputRef.current && options.length !== prevOptionsLengthRef.current) {
      setTimeout(() => {
        if (inputRef.current && isOpen) {
          inputRef.current.focus();
        }
      }, 0);
    }
    prevOptionsLengthRef.current = options.length;
  }, [options, isOpen]);

  // Handle opening the dropdown
  const handleOpen = () => {
    if (isDisabled) return;
    onOpen();
    setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
  };

  // Clear search when dropdown closes
  const handleClose = () => {
    setSearchTerm('');
    onClose();
  };

  // Handle search term change and trigger onSearch callback
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newSearchTerm = e.target.value;
    setSearchTerm(newSearchTerm);
    if (onSearch) {
      onSearch(newSearchTerm);
    }
  };

  // Filter options based on search term
  const filteredOptions = useMemo(() => {
    if (!searchTerm.trim()) {
      return options;
    }

    const searchLower = searchTerm.toLowerCase();
    return options.filter((option) => {
      const labelMatch = option.label && option.label.toLowerCase().includes(searchLower);
      const valueMatch = option.value && option.value.toLowerCase().includes(searchLower);
      return labelMatch || valueMatch;
    });
  }, [options, searchTerm]);

  // Handle option selection
  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    handleClose();
  };

  // Get display text
  const getDisplayText = () => {
    if (!value) return placeholder;
    const selectedOption = options.find((opt) => opt.value === value);
    return selectedOption ? selectedOption.label : value;
  };

  // Get size-specific styles
  const getSizeStyles = () => {
    switch (size) {
      case 'xs':
        return { fontSize: 'sm', h: '24px', py: 0, px: 2 };
      case 'sm':
        return { fontSize: 'md', h: '36px', py: 2, px: 3, fontWeight: 'medium' };
      case 'md':
        return { fontSize: 'md', h: '40px', py: 2, px: 4 };
      case 'lg':
        return { fontSize: 'lg', h: '48px', py: 3, px: 4 };
      default:
        return { fontSize: 'sm', h: '24px', py: 0, px: 2 };
    }
  };

  const sizeStyles = getSizeStyles();

  return (
    <Box position="relative" ref={containerRef}>
      {/* Display Input (not editable, just for display) */}
      <Box
        onClick={handleOpen}
        cursor={isDisabled ? 'not-allowed' : 'pointer'}
        opacity={isDisabled ? 0.6 : 1}
      >
        <InputGroup size={size}>
          <Input
            value={getDisplayText()}
            readOnly
            placeholder={placeholder}
            {...sizeStyles}
            bg={value ? 'white' : 'blue.50'}
            borderColor="blue.500"
            borderWidth="2px"
            fontWeight={value ? 'semibold' : 'medium'}
            color={value ? 'blue.800' : 'blue.600'}
            _placeholder={{ color: 'blue.500', fontWeight: 'medium' }}
            _hover={{ 
              borderColor: isDisabled ? 'blue.500' : 'blue.600',
              bg: isDisabled ? (value ? 'white' : 'blue.50') : 'blue.100',
              transform: 'scale(1.01)',
              shadow: 'md'
            }}
            _focus={{ 
              borderColor: 'blue.600',
              boxShadow: '0 0 0 3px var(--chakra-colors-blue-200)'
            }}
            cursor={isDisabled ? 'not-allowed' : 'pointer'}
            transition="all 0.2s"
          />
          <InputRightElement h={sizeStyles.h} pointerEvents="none">
            <Icon as={ChevronDownIcon} color="blue.700" boxSize={5} fontWeight="bold" />
          </InputRightElement>
        </InputGroup>
      </Box>

      {/* Dropdown */}
      {isOpen && (
        <Box
          ref={dropdownRef}
          position="fixed"
          top={`${containerRef.current?.getBoundingClientRect().bottom || 0}px`}
          left={`${containerRef.current?.getBoundingClientRect().left || 0}px`}
          width={`${containerRef.current?.getBoundingClientRect().width || 200}px`}
          mt={1}
          bg="white"
          borderWidth="2px"
          borderColor="blue.400"
          borderRadius="md"
          shadow="2xl"
          zIndex={9999}
          maxH="300px"
          overflow="hidden"
        >
          {/* Search Input */}
          <Box p={3} borderBottomWidth="2px" borderColor="blue.100" bg="blue.50">
            <InputGroup size="sm">
              <InputLeftElement pointerEvents="none">
                <Icon as={SearchIcon} color="blue.500" />
              </InputLeftElement>
              <Input
                ref={inputRef}
                placeholder="Search by name or email..."
                value={searchTerm}
                onChange={handleSearchChange}
                autoFocus
                bg="white"
                borderColor="blue.300"
                _focus={{
                  borderColor: 'blue.500',
                  boxShadow: '0 0 0 1px var(--chakra-colors-blue-500)'
                }}
              />
              {isLoading && (
                <InputRightElement>
                  <Spinner size="sm" color="blue.500" />
                </InputRightElement>
              )}
            </InputGroup>
          </Box>

          {/* Options List */}
          <Box
            ref={scrollContainerRef}
            maxH="240px"
            overflowY="auto"
            onScroll={(e) => {
              // Stop propagation to prevent window scroll handler from closing dropdown
              e.stopPropagation();
            }}
          >
            <VStack align="stretch" spacing={0}>
            {filteredOptions.length === 0 ? (
              <Box p={4} textAlign="center" bg="gray.50">
                <Text fontSize="sm" color="gray.600" fontWeight="medium">
                  {isLoading ? 'Searching...' : emptyMessage}
                </Text>
              </Box>
            ) : (
              filteredOptions.map((option) => (
                <HStack
                  key={option.value}
                  px={4}
                  py={3}
                  cursor="pointer"
                  _hover={{ bg: 'blue.100', borderLeftWidth: '3px', borderLeftColor: 'blue.500' }}
                  bg={value === option.value ? 'blue.50' : 'white'}
                  borderBottomWidth="1px"
                  borderColor="gray.100"
                  onClick={() => handleSelect(option.value)}
                  spacing={3}
                  transition="all 0.2s"
                >
                  <VStack align="start" spacing={0.5} flex={1}>
                    <Text 
                      fontSize="sm" 
                      fontWeight={value === option.value ? 'bold' : 'semibold'}
                      color={value === option.value ? 'blue.700' : 'gray.800'}
                    >
                      {option.label}
                    </Text>
                    <Text fontSize="xs" color="gray.600" fontWeight="medium">
                      {option.value}
                    </Text>
                  </VStack>
                  {value === option.value && (
                    <Box w={3} h={3} borderRadius="full" bg="blue.600" border="2px" borderColor="blue.200" />
                  )}
                </HStack>
              ))
            )}
            </VStack>
          </Box>
        </Box>
      )}
    </Box>
  );
};

