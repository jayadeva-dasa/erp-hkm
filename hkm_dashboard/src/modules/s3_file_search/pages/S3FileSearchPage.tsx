// S3 File Search Page

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  VStack,
  Heading,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  useToast,
  Spinner,
  HStack,
  Badge,
  Icon,
  IconButton,
  Tooltip,
  Flex,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Card,
  CardBody,
  useColorModeValue,
  Link,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiDownload,
  FiEye,
  FiFilter,
  FiRefreshCw,
  FiFile,
  FiImage,
  FiFileText,
  FiVideo,
  FiDatabase,
} from 'react-icons/fi';
import { s3FileSearchApi } from '../api/s3FileSearchApi';
import type { S3File, S3SearchFilters, S3Stats } from '../types';
import { FilePreviewModal } from '../components/FilePreviewModal';
import { FileFilters } from '../components/FileFilters';

const S3FileSearchPage: React.FC = () => {
  const [files, setFiles] = useState<S3File[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [filters, setFilters] = useState<S3SearchFilters>({});
  const [showFilters, setShowFilters] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<S3File | null>(null);
  const [isPreviewOpen, setIsPreviewOpen] = useState(false);
  const [stats, setStats] = useState<S3Stats | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [filteredCount, setFilteredCount] = useState<number>(0);
  
  const toast = useToast();
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const statsData = await s3FileSearchApi.getStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleSearch = useCallback(async () => {
    try {
      setLoading(true);
      const searchFilters: S3SearchFilters = {
        ...filters,
        search_term: searchTerm,
      };

      const response = await s3FileSearchApi.searchFiles(searchFilters);
      
      if (response.success) {
        setFiles(response.files);
        setTotalCount(response.total_count);
        setFilteredCount(response.filtered_count);
        
        toast({
          title: 'Search completed',
          description: `Found ${response.filtered_count} files`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error(response.error || 'Search failed');
      }
    } catch (error: any) {
      toast({
        title: 'Search failed',
        description: error.message || 'An error occurred',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  }, [searchTerm, filters, toast]);

  const handleDownload = (file: S3File) => {
    try {
      s3FileSearchApi.downloadFile(file.key, file.file_name);
      toast({
        title: 'Download started',
        description: file.file_name,
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    } catch (error: any) {
      toast({
        title: 'Download failed',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handlePreview = (file: S3File) => {
    setSelectedFile(file);
    setIsPreviewOpen(true);
  };

  const handleClearFilters = () => {
    setFilters({});
    setSearchTerm('');
    setFiles([]);
  };

  const getFileIcon = (fileType: string) => {
    if (fileType.startsWith('image/')) return FiImage;
    if (fileType === 'application/pdf') return FiFileText;
    if (fileType.startsWith('video/')) return FiVideo;
    return FiFile;
  };

  const getFileTypeColor = (fileType: string): string => {
    if (fileType.startsWith('image/')) return 'purple';
    if (fileType === 'application/pdf') return 'red';
    if (fileType.startsWith('video/')) return 'blue';
    if (fileType.includes('spreadsheet') || fileType.includes('excel')) return 'green';
    if (fileType.includes('document') || fileType.includes('word')) return 'blue';
    return 'gray';
  };

  return (
    <Container maxW="container.xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <Heading size="lg" mb={2}>
            S3 File Search
          </Heading>
          <Text color="gray.600">
            Search and browse files stored in the S3 bucket
          </Text>
        </Box>

        {/* Stats */}
        {stats && (
          <Card>
            <CardBody>
              <StatGroup>
                <Stat>
                  <StatLabel>Total Files</StatLabel>
                  <StatNumber>{stats.total_files.toLocaleString()}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Total Size</StatLabel>
                  <StatNumber>{stats.total_size_formatted}</StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Images</StatLabel>
                  <StatNumber>
                    {(stats.file_types['image'] || 0).toLocaleString()}
                  </StatNumber>
                </Stat>
                <Stat>
                  <StatLabel>Documents</StatLabel>
                  <StatNumber>
                    {(stats.file_types['document'] || 0).toLocaleString()}
                  </StatNumber>
                </Stat>
              </StatGroup>
            </CardBody>
          </Card>
        )}

        {/* Search Bar */}
        <Card>
          <CardBody>
            <VStack spacing={4}>
              <HStack width="100%" spacing={4}>
                <InputGroup flex={1}>
                  <InputLeftElement>
                    <Icon as={FiSearch} color="gray.400" />
                  </InputLeftElement>
                  <Input
                    placeholder="Search files by name..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  />
                </InputGroup>
                
                <Button
                  colorScheme="blue"
                  leftIcon={<FiSearch />}
                  onClick={handleSearch}
                  isLoading={loading}
                  loadingText="Searching..."
                >
                  Search
                </Button>
                
                <IconButton
                  aria-label="Toggle filters"
                  icon={<FiFilter />}
                  variant={showFilters ? 'solid' : 'outline'}
                  colorScheme="gray"
                  onClick={() => setShowFilters(!showFilters)}
                />
                
                <IconButton
                  aria-label="Refresh stats"
                  icon={<FiRefreshCw />}
                  variant="outline"
                  onClick={loadStats}
                />
              </HStack>

              {/* Filters */}
              <FileFilters
                filters={filters}
                onFilterChange={setFilters}
                onClearFilters={handleClearFilters}
                isOpen={showFilters}
              />
            </VStack>
          </CardBody>
        </Card>

        {/* Results Summary */}
        {files.length > 0 && (
          <HStack justify="space-between">
            <Text color="gray.600">
              Showing {filteredCount} of {totalCount} files
            </Text>
            {searchTerm && (
              <Badge colorScheme="blue" fontSize="sm">
                Search: "{searchTerm}"
              </Badge>
            )}
          </HStack>
        )}

        {/* Results Table */}
        {loading ? (
          <Flex justify="center" align="center" py={20}>
            <VStack spacing={4}>
              <Spinner size="xl" color="blue.500" thickness="4px" />
              <Text color="gray.600">Searching files...</Text>
            </VStack>
          </Flex>
        ) : files.length > 0 ? (
          <Card>
            <CardBody p={0}>
              <TableContainer>
                <Table variant="simple">
                  <Thead bg="gray.50">
                    <Tr>
                      <Th>File Name</Th>
                      <Th>Type</Th>
                      <Th>Size</Th>
                      <Th>Last Modified</Th>
                      <Th>Folder</Th>
                      <Th textAlign="right">Actions</Th>
                    </Tr>
                  </Thead>
                  <Tbody>
                    {files.map((file, index) => (
                      <Tr key={index} _hover={{ bg: 'gray.50' }}>
                        <Td>
                          <HStack>
                            <Icon
                              as={getFileIcon(file.file_type)}
                              color={`${getFileTypeColor(file.file_type)}.500`}
                            />
                            <Text fontWeight="medium">{file.file_name}</Text>
                          </HStack>
                        </Td>
                        <Td>
                          <Badge colorScheme={getFileTypeColor(file.file_type)}>
                            {file.file_type.split('/')[1] || 'unknown'}
                          </Badge>
                        </Td>
                        <Td>
                          <Text fontSize="sm">{file.size_formatted}</Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.600">
                            {file.last_modified_formatted}
                          </Text>
                        </Td>
                        <Td>
                          <Text fontSize="sm" color="gray.600" isTruncated maxW="200px">
                            {file.folder_path || '/'}
                          </Text>
                        </Td>
                        <Td textAlign="right">
                          <HStack spacing={2} justify="flex-end">
                            <Tooltip label="Preview">
                              <IconButton
                                aria-label="Preview file"
                                icon={<FiEye />}
                                size="sm"
                                variant="ghost"
                                onClick={() => handlePreview(file)}
                              />
                            </Tooltip>
                            <Tooltip label="Download">
                              <IconButton
                                aria-label="Download file"
                                icon={<FiDownload />}
                                size="sm"
                                variant="ghost"
                                colorScheme="blue"
                                onClick={() => handleDownload(file)}
                              />
                            </Tooltip>
                          </HStack>
                        </Td>
                      </Tr>
                    ))}
                  </Tbody>
                </Table>
              </TableContainer>
            </CardBody>
          </Card>
        ) : searchTerm || Object.keys(filters).length > 0 ? (
          <Card>
            <CardBody>
              <VStack spacing={4} py={12}>
                <Icon as={FiSearch} boxSize={16} color="gray.300" />
                <Text color="gray.600" fontSize="lg">
                  No files found
                </Text>
                <Text color="gray.500" fontSize="sm">
                  Try adjusting your search or filters
                </Text>
              </VStack>
            </CardBody>
          </Card>
        ) : (
          <Card>
            <CardBody>
              <VStack spacing={4} py={12}>
                <Icon as={FiDatabase} boxSize={16} color="gray.300" />
                <Text color="gray.600" fontSize="lg">
                  Start searching
                </Text>
                <Text color="gray.500" fontSize="sm">
                  Enter a search term to find files in the S3 bucket
                </Text>
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>

      {/* Preview Modal */}
      <FilePreviewModal
        isOpen={isPreviewOpen}
        onClose={() => setIsPreviewOpen(false)}
        file={selectedFile}
        onDownload={handleDownload}
      />
    </Container>
  );
};

export default S3FileSearchPage;

