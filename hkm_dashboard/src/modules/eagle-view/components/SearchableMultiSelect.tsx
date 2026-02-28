// Searchable Multi-Select Component for Eagle View
import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Box,
  Button,
  Checkbox,
  Input,
  InputGroup,
  InputLeftElement,
  VStack,
  Text,
  Icon,
  HStack,
  Badge,
  Flex,
  useDisclosure,
  Portal,
} from '@chakra-ui/react';
import { SearchIcon, ChevronDownIcon } from '@chakra-ui/icons';

interface Option {
  value: string;
  label: string;
}

interface SearchableMultiSelectProps {
  options: Option[];
  value: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
  label?: string;
  onOpen?: () => void;
  onSearch?: (searchTerm: string) => void;
  isLoading?: boolean;
}

export const SearchableMultiSelect: React.FC<SearchableMultiSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  label,
  onOpen: onOpenCallback,
  onSearch,
  isLoading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const { isOpen, onOpen, onClose } = useDisclosure();
  const inputRef = useRef<HTMLInputElement>(null);
  const prevOptionsLengthRef = useRef<number>(options.length);
  
  // When options change (backend results arrive), maintain focus on input
  useEffect(() => {
    if (isOpen && inputRef.current && options.length !== prevOptionsLengthRef.current) {
      // Options updated (backend search completed), keep focus on input
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        if (inputRef.current && isOpen) {
          inputRef.current.focus();
        }
      }, 0);
    }
    prevOptionsLengthRef.current = options.length;
  }, [options, isOpen]);
  
  // Call onOpen callback when popover opens
  const handleOpen = () => {
    onOpen();
    if (onOpenCallback) {
      onOpenCallback();
    }
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
    // Trigger backend search if callback provided
    if (onSearch) {
      onSearch(newSearchTerm);
    }
  };

  // Filter options based on search term and sort: selected first, then alphabetically
  // Strategy: Always do client-side filtering for instant feedback
  // Backend search (if enabled) will update the options prop with refined results
  const filteredOptions = useMemo(() => {
    let optionsToShow = options;
    
    // Always do client-side filtering if there's a search term
    // This provides instant feedback while backend search is in progress
    if (searchTerm.trim()) {
      const searchLower = searchTerm.toLowerCase();
      optionsToShow = options.filter((option) => {
        const labelMatch = option.label && option.label.toLowerCase().includes(searchLower);
        const valueMatch = option.value && option.value.toLowerCase().includes(searchLower);
        return labelMatch || valueMatch;
      });
    }
    
    // Sort: selected items first, then unselected (both alphabetically)
    return optionsToShow.sort((a, b) => {
      const aSelected = value.includes(a.value);
      const bSelected = value.includes(b.value);
      
      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;
      
      // Both selected or both unselected - sort alphabetically
      return a.label.localeCompare(b.label);
    });
  }, [options, searchTerm, value]);

  // Handle option toggle
  const handleToggle = (optionValue: string, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (value.includes(optionValue)) {
      const newValue = value.filter((v) => v !== optionValue);
      onChange(newValue);
    } else {
      const newValue = [...value, optionValue];
      onChange(newValue);
    }
  };

  // Handle clear all
  const handleClearAll = () => {
    onChange([]);
    setSearchTerm('');
  };

  // Get display text
  const getDisplayText = () => {
    if (value.length === 0) return placeholder;
    if (value.length === 1) {
      const option = options.find((o) => o.value === value[0]);
      return option ? option.label : '';
    }
    return `${value.length} values selected`;
  };

  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0 });

  // Calculate position when dropdown opens
  useEffect(() => {
    if (isOpen && triggerRef.current) {
      const updatePosition = () => {
        if (triggerRef.current) {
          const rect = triggerRef.current.getBoundingClientRect();
          const scrollY = window.scrollY || window.pageYOffset;
          const scrollX = window.scrollX || window.pageXOffset;
          
          setPosition({
            top: rect.bottom + scrollY + 4,
            left: rect.left + scrollX,
            width: Math.max(rect.width, 400),
          });
        }
      };
      
      updatePosition();
      window.addEventListener('scroll', updatePosition, true);
      window.addEventListener('resize', updatePosition);
      
      return () => {
        window.removeEventListener('scroll', updatePosition, true);
        window.removeEventListener('resize', updatePosition);
      };
    }
  }, [isOpen]);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (
        isOpen &&
        dropdownRef.current &&
        triggerRef.current &&
        !dropdownRef.current.contains(target) &&
        !triggerRef.current.contains(target)
      ) {
        // Small delay to ensure click events on options are processed first
        requestAnimationFrame(() => {
          if (isOpen) {
            handleClose();
          }
        });
      }
    };

    if (isOpen) {
      // Use a slight delay to ensure the click event on the option is processed first
      const timeoutId = setTimeout(() => {
        document.addEventListener('click', handleClickOutside, true);
      }, 0);
      
      return () => {
        clearTimeout(timeoutId);
        document.removeEventListener('click', handleClickOutside, true);
      };
    }
  }, [isOpen, handleClose]);

  return (
    <Box position="relative" zIndex={10} overflow="visible">
      <Button
        ref={triggerRef}
        width="100%"
        justifyContent="space-between"
        rightIcon={<ChevronDownIcon />}
        variant="outline"
        size="sm"
        fontWeight="normal"
        bg="white"
        textAlign="left"
        _hover={{ bg: 'gray.50' }}
        onClick={handleOpen}
      >
        <Text isTruncated maxW="90%">
          {getDisplayText()}
        </Text>
      </Button>

      {isOpen && (
        <Portal>
          <Box
            ref={dropdownRef}
            position="fixed"
            top={`${position.top}px`}
            left={`${position.left}px`}
            width={`${Math.min(position.width, window.innerWidth - position.left - 16)}px`}
            maxW="calc(100vw - 32px)"
            maxH="400px"
            zIndex={10000}
            boxShadow="xl"
            border="1px solid"
            borderColor="gray.200"
            bg="white"
            borderRadius="md"
            overflow="hidden"
          >
            <VStack spacing={0} align="stretch" overflow="hidden" display="flex" flexDirection="column" maxH="400px">
              {/* Search Box */}
              <Box p={3} borderBottom="1px" borderColor="gray.200" flexShrink={0}>
                <InputGroup size="sm">
                  <InputLeftElement pointerEvents="none">
                    <Icon as={SearchIcon} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    ref={inputRef}
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={handleSearchChange}
                    bg="white"
                    isDisabled={isLoading}
                    autoFocus
                  />
                </InputGroup>
              </Box>

              {/* Selected Count */}
              {value.length > 0 && (
                <Box px={3} py={2} bg="blue.50" borderBottom="1px" borderColor="gray.200" flexShrink={0}>
                  <HStack justify="space-between">
                    <Badge colorScheme="blue">{value.length} selected</Badge>
                    <Button
                      size="xs"
                      colorScheme="orange"
                      onClick={handleClearAll}
                    >
                      Clear All
                    </Button>
                  </HStack>
                </Box>
              )}

              {/* Options List */}
              <Box 
                maxH="300px" 
                overflowY="auto" 
                overflowX="hidden"
                flex="1"
                minH="0"
              >
                {filteredOptions.length === 0 ? (
                  <Box p={4} textAlign="center">
                    <Text color="gray.500" fontSize="sm">
                      No options found
                    </Text>
                  </Box>
                ) : (
                  <VStack spacing={0} align="stretch">
                    {filteredOptions.map((option) => (
                      <Flex
                        key={option.value}
                        px={3}
                        py={2}
                        cursor="pointer"
                        _hover={{ bg: 'gray.50' }}
                        borderBottom="1px"
                        borderColor="gray.100"
                        alignItems="center"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleToggle(option.value, e);
                        }}
                      >
                        <Checkbox
                          isChecked={value.includes(option.value)}
                          onChange={() => {
                            handleToggle(option.value);
                          }}
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                          }}
                          mr={2}
                        />
                        <Text fontSize="sm" userSelect="none" flex="1">
                          {option.label}
                        </Text>
                      </Flex>
                    ))}
                  </VStack>
                )}
              </Box>
            </VStack>
          </Box>
        </Portal>
      )}
    </Box>
  );
};

