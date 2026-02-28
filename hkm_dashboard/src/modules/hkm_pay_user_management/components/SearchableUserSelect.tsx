import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Input,
  List,
  ListItem,
  FormControl,
  FormLabel,
  Text,
  Flex,
  useColorModeValue,
  InputGroup,
  InputLeftElement,
  Spinner,
} from '@chakra-ui/react';
import { FiSearch, FiUser } from 'react-icons/fi';
import { hkmpUserApi } from '../api/hkmpUserApi';

interface User {
  name: string;
  full_name: string;
}

interface SearchableUserSelectProps {
  initialUsers?: User[];
  value: string;
  onChange: (value: string, user?: User) => void;
  isDisabled?: boolean;
  placeholder?: string;
  isRequired?: boolean;
  label?: string;
}

const SearchableUserSelect: React.FC<SearchableUserSelectProps> = ({
  initialUsers = [],
  value,
  onChange,
  isDisabled = false,
  placeholder = 'Search and select user',
  isRequired = false,
  label = 'User',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [users, setUsers] = useState<User[]>(initialUsers);
  const [selectedUserData, setSelectedUserData] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [displayLimit] = useState(30);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');
  const selectedBg = useColorModeValue('blue.50', 'blue.900');

  // Get selected user's display text from stored selected user data
  const displayText = selectedUserData 
    ? `${selectedUserData.full_name} (${selectedUserData.name})`
    : '';

  // Fetch users from API when search term changes
  useEffect(() => {
    // Clear previous timeout
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce search - wait 300ms after user stops typing
    searchTimeoutRef.current = setTimeout(async () => {
      setIsLoading(true);
      try {
        const fetchedUsers = await hkmpUserApi.getAllSystemUsers(
          searchTerm || undefined, 
          displayLimit
        );
        setUsers(fetchedUsers);
      } catch (error) {
        console.error('Error fetching users:', error);
        setUsers([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchTerm, displayLimit]);

  // Clear selected user data when value is cleared from outside
  useEffect(() => {
    if (!value) {
      setSelectedUserData(null);
    }
  }, [value]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleUserSelect = (user: User) => {
    // Store the selected user data before closing dropdown
    setSelectedUserData(user);
    onChange(user.name, user);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleInputClick = () => {
    if (!isDisabled) {
      setIsOpen(true);
      // Clear search term when opening to show fresh results
      setSearchTerm('');
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    if (!isOpen) {
      setIsOpen(true);
    }
  };

  return (
    <FormControl isRequired={isRequired} ref={wrapperRef}>
      <FormLabel>{label}</FormLabel>
      <Box position="relative">
        <InputGroup>
          <InputLeftElement pointerEvents="none">
            <FiSearch color="gray.300" />
          </InputLeftElement>
          <Input
            placeholder={placeholder}
            value={isOpen ? searchTerm : displayText}
            onChange={handleInputChange}
            onClick={handleInputClick}
            isDisabled={isDisabled}
            autoComplete="off"
            bg={bgColor}
          />
        </InputGroup>

        {/* Dropdown List */}
        {isOpen && !isDisabled && (
          <Box
            position="absolute"
            top="100%"
            left={0}
            right={0}
            zIndex={1000}
            mt={1}
            maxH="300px"
            overflowY="auto"
            bg={bgColor}
            border="1px solid"
            borderColor={borderColor}
            borderRadius="md"
            boxShadow="lg"
          >
            {isLoading ? (
              <Box p={4} textAlign="center">
                <Spinner size="md" color="blue.500" />
                <Text color="gray.500" mt={2}>Searching users...</Text>
              </Box>
            ) : users.length === 0 ? (
              <Box p={4} textAlign="center">
                <Text color="gray.500">No users found</Text>
                {searchTerm && (
                  <Text fontSize="sm" color="gray.400" mt={1}>
                    Try a different search term
                  </Text>
                )}
              </Box>
            ) : (
              <>
                <List spacing={0}>
                  {users.map((user) => (
                    <ListItem
                      key={user.name}
                      px={4}
                      py={3}
                      cursor="pointer"
                      bg={value === user.name ? selectedBg : 'transparent'}
                      _hover={{ bg: hoverBg }}
                      onClick={() => handleUserSelect(user)}
                      borderBottom="1px solid"
                      borderColor={borderColor}
                    >
                      <Flex align="center" gap={2}>
                        <FiUser />
                        <Box flex={1}>
                          <Text fontWeight="medium">{user.full_name}</Text>
                          <Text fontSize="sm" color="gray.500">
                            {user.name}
                          </Text>
                        </Box>
                      </Flex>
                    </ListItem>
                  ))}
                </List>
                {users.length === displayLimit && (
                  <Box
                    p={2}
                    textAlign="center"
                    bg={useColorModeValue('gray.50', 'gray.900')}
                    borderTop="1px solid"
                    borderColor={borderColor}
                  >
                    <Text fontSize="xs" color="gray.500">
                      Showing first {displayLimit} results
                      {searchTerm && ' - refine your search to see more'}
                    </Text>
                  </Box>
                )}
              </>
            )}
          </Box>
        )}
      </Box>
    </FormControl>
  );
};

export default SearchableUserSelect;

