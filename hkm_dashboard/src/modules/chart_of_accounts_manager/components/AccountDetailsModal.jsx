import React, { useEffect, useState } from 'react';
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
  HStack,
  Text,
  Badge,
  Divider,
  Box,
  Spinner,
  useColorModeValue,
  Table,
  Tbody,
  Tr,
  Td,
  Link,
  Icon,
} from '@chakra-ui/react';
import { FiExternalLink } from 'react-icons/fi';
import { getAccountDetails } from '../api/chartOfAccountsApi';
import { formatCurrency, getAccountTypeColor, getAccountPath } from '../utils/accountUtils';

const AccountDetailsModal = ({ isOpen, onClose, account, company, asOnDate, allAccounts }) => {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const bgColor = useColorModeValue('gray.50', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  
  useEffect(() => {
    if (isOpen && account && company) {
      loadAccountDetails();
    }
  }, [isOpen, account, company, asOnDate]);
  
  const loadAccountDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getAccountDetails(account.name, company, asOnDate, asOnDate);
      setDetails(data);
    } catch (err) {
      console.error('Error loading account details:', err);
      setError(err.message || 'Failed to load account details');
    } finally {
      setLoading(false);
    }
  };
  
  const accountTypeColor = getAccountTypeColor(account?.root_type);
  const accountPath = allAccounts ? getAccountPath(allAccounts, account?.name) : [];
  
  const openInERPNext = () => {
    if (account) {
      window.open(`/app/account/${encodeURIComponent(account.name)}`, '_blank');
    }
  };
  
  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <VStack align="start" spacing={0}>
            <Text fontSize="lg" fontWeight="bold">
              {account?.account_name}
            </Text>
            {account?.account_number && (
              <Text fontSize="sm" color="gray.500">
                {account.account_number}
              </Text>
            )}
          </VStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {loading ? (
            <Box textAlign="center" py={8}>
              <Spinner size="xl" color="blue.500" />
              <Text mt={4} color="gray.500">Loading account details...</Text>
            </Box>
          ) : error ? (
            <Box textAlign="center" py={8}>
              <Text color="red.500">{error}</Text>
              <Button mt={4} onClick={loadAccountDetails} size="sm">
                Retry
              </Button>
            </Box>
          ) : (
            <VStack spacing={4} align="stretch">
              {/* Account Path */}
              {accountPath.length > 0 && (
                <Box bg={bgColor} p={3} borderRadius="md">
                  <Text fontSize="xs" fontWeight="medium" color="gray.500" mb={1}>
                    ACCOUNT PATH
                  </Text>
                  <Text fontSize="sm">
                    {accountPath.join(' > ')}
                  </Text>
                </Box>
              )}
              
              {/* Basic Info */}
              <Box bg={bgColor} p={4} borderRadius="md">
                <Table size="sm" variant="simple">
                  <Tbody>
                    <Tr>
                      <Td fontWeight="medium" w="40%">Account Type</Td>
                      <Td>
                        <Badge colorScheme={accountTypeColor}>
                          {account?.root_type}
                        </Badge>
                      </Td>
                    </Tr>
                    {account?.account_type && (
                      <Tr>
                        <Td fontWeight="medium">Sub Type</Td>
                        <Td>{account.account_type}</Td>
                      </Tr>
                    )}
                    <Tr>
                      <Td fontWeight="medium">Is Group</Td>
                      <Td>
                        <Badge colorScheme={account?.is_group ? 'green' : 'gray'}>
                          {account?.is_group ? 'Yes' : 'No'}
                        </Badge>
                      </Td>
                    </Tr>
                    {account?.parent_account && (
                      <Tr>
                        <Td fontWeight="medium">Parent Account</Td>
                        <Td>{account.parent_account}</Td>
                      </Tr>
                    )}
                    <Tr>
                      <Td fontWeight="medium">Company</Td>
                      <Td>{account?.company}</Td>
                    </Tr>
                  </Tbody>
                </Table>
              </Box>
              
              {/* Balance Information */}
              {details && (
                <Box bg={bgColor} p={4} borderRadius="md">
                  <Text fontSize="sm" fontWeight="bold" mb={3}>
                    Balance Information
                  </Text>
                  <Table size="sm" variant="simple">
                    <Tbody>
                      <Tr>
                        <Td fontWeight="medium" w="40%">Opening Balance</Td>
                        <Td textAlign="right" fontWeight="medium">
                          {formatCurrency(details.opening_balance || 0, details.currency)}
                        </Td>
                      </Tr>
                      <Tr>
                        <Td fontWeight="medium">Debit</Td>
                        <Td textAlign="right" color="green.600">
                          {formatCurrency(details.debit || 0, details.currency)}
                        </Td>
                      </Tr>
                      <Tr>
                        <Td fontWeight="medium">Credit</Td>
                        <Td textAlign="right" color="red.600">
                          {formatCurrency(details.credit || 0, details.currency)}
                        </Td>
                      </Tr>
                      <Tr borderTopWidth="2px" borderColor={borderColor}>
                        <Td fontWeight="bold">Closing Balance</Td>
                        <Td
                          textAlign="right"
                          fontWeight="bold"
                          fontSize="lg"
                          color={details.closing_balance >= 0 ? 'green.600' : 'red.600'}
                        >
                          {formatCurrency(details.closing_balance || 0, details.currency)}
                        </Td>
                      </Tr>
                    </Tbody>
                  </Table>
                  
                  <Text fontSize="xs" color="gray.500" mt={2}>
                    As On: {asOnDate}
                  </Text>
                </Box>
              )}
              
              {/* Additional Info */}
              {details?.report_type && (
                <Box bg={bgColor} p={3} borderRadius="md">
                  <Text fontSize="xs" fontWeight="medium" color="gray.500" mb={1}>
                    REPORT TYPE
                  </Text>
                  <Text fontSize="sm">{details.report_type}</Text>
                </Box>
              )}
            </VStack>
          )}
        </ModalBody>
        
        <ModalFooter>
          <HStack spacing={3}>
            <Button
              leftIcon={<FiExternalLink />}
              colorScheme="blue"
              variant="outline"
              onClick={openInERPNext}
              size="sm"
            >
              Open in ERPNext
            </Button>
            <Button onClick={onClose} size="sm">
              Close
            </Button>
          </HStack>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AccountDetailsModal;
