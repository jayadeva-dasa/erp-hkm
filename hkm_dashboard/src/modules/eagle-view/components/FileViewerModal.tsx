import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  Box,
  Image,
  VStack,
  HStack,
  Text,
  IconButton,
  Badge,
  Link,
  useColorModeValue,
} from '@chakra-ui/react';
import { DownloadIcon, ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';

interface Attachment {
  file_name: string;
  file_url: string;
  file_size: number;
  is_private: number;
  file_type: 'pdf' | 'image' | 'other';
}

interface FileViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  attachments: Attachment[];
  voucherNo: string;
}

export const FileViewerModal: React.FC<FileViewerModalProps> = ({
  isOpen,
  onClose,
  attachments,
  voucherNo,
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  if (!attachments || attachments.length === 0) {
    return null;
  }

  const currentFile = attachments[currentIndex];

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : attachments.length - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < attachments.length - 1 ? prev + 1 : 0));
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i];
  };

  const getFullUrl = (url: string) => {
    // Ensure URL is absolute
    if (url.startsWith('http')) return url;
    return `${window.location.origin}${url}`;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl" isCentered>
      <ModalOverlay bg="blackAlpha.800" backdropFilter="blur(10px)" />
      <ModalContent maxW="90vw" maxH="90vh">
        <ModalHeader>
          <VStack align="start" spacing={2}>
            <HStack>
              <Text>Attachments - {voucherNo}</Text>
              {attachments.length > 1 && (
                <Badge colorScheme="blue">
                  {currentIndex + 1} of {attachments.length}
                </Badge>
              )}
            </HStack>
            <HStack spacing={2} fontSize="sm" color="gray.600">
              <Text fontWeight="normal">{currentFile.file_name}</Text>
              <Badge>{formatFileSize(currentFile.file_size)}</Badge>
              <Link
                href={getFullUrl(currentFile.file_url)}
                download
                isExternal
              >
                <IconButton
                  aria-label="Download"
                  icon={<DownloadIcon />}
                  size="sm"
                  colorScheme="green"
                  variant="ghost"
                />
              </Link>
            </HStack>
          </VStack>
        </ModalHeader>
        <ModalCloseButton />

        <ModalBody pb={6}>
          <HStack spacing={2} align="stretch" h="70vh">
            {/* Navigation - Previous */}
            {attachments.length > 1 && (
              <Box display="flex" alignItems="center">
                <IconButton
                  aria-label="Previous"
                  icon={<ChevronLeftIcon boxSize={8} />}
                  onClick={handlePrevious}
                  variant="ghost"
                  size="lg"
                />
              </Box>
            )}

            {/* File Viewer */}
            <Box
              flex="1"
              bg={bgColor}
              borderWidth="1px"
              borderColor={borderColor}
              borderRadius="md"
              overflow="auto"
              display="flex"
              alignItems="center"
              justifyContent="center"
            >
              {currentFile.file_type === 'image' && (
                <Image
                  src={getFullUrl(currentFile.file_url)}
                  alt={currentFile.file_name}
                  maxH="100%"
                  maxW="100%"
                  objectFit="contain"
                />
              )}

              {currentFile.file_type === 'pdf' && (
                <Box w="100%" h="100%">
                  <iframe
                    src={`${getFullUrl(currentFile.file_url)}#toolbar=1`}
                    width="100%"
                    height="100%"
                    title={currentFile.file_name}
                    style={{ border: 'none' }}
                  />
                </Box>
              )}

              {currentFile.file_type === 'other' && (
                <VStack spacing={4} p={8}>
                  <Text fontSize="lg" fontWeight="bold">
                    {currentFile.file_name}
                  </Text>
                  <Text color="gray.600">
                    Preview not available for this file type
                  </Text>
                  <Link
                    href={getFullUrl(currentFile.file_url)}
                    download
                  >
                    <IconButton
                      aria-label="Download"
                      icon={<DownloadIcon />}
                      colorScheme="green"
                      size="lg"
                    >
                      Download File
                    </IconButton>
                  </Link>
                </VStack>
              )}
            </Box>

            {/* Navigation - Next */}
            {attachments.length > 1 && (
              <Box display="flex" alignItems="center">
                <IconButton
                  aria-label="Next"
                  icon={<ChevronRightIcon boxSize={8} />}
                  onClick={handleNext}
                  variant="ghost"
                  size="lg"
                />
              </Box>
            )}
          </HStack>

          {/* Thumbnail Strip for Multiple Files */}
          {attachments.length > 1 && (
            <HStack
              mt={4}
              spacing={2}
              overflowX="auto"
              py={2}
              css={{
                '&::-webkit-scrollbar': {
                  height: '8px',
                },
                '&::-webkit-scrollbar-track': {
                  background: '#f1f1f1',
                },
                '&::-webkit-scrollbar-thumb': {
                  background: '#888',
                  borderRadius: '4px',
                },
              }}
            >
              {attachments.map((att, index) => (
                <Box
                  key={index}
                  minW="80px"
                  h="60px"
                  borderWidth="2px"
                  borderColor={index === currentIndex ? 'blue.500' : borderColor}
                  borderRadius="md"
                  cursor="pointer"
                  onClick={() => setCurrentIndex(index)}
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  bg={bgColor}
                  p={1}
                  transition="all 0.2s"
                  _hover={{ borderColor: 'blue.300' }}
                >
                  {att.file_type === 'image' ? (
                    <Image
                      src={getFullUrl(att.file_url)}
                      alt={att.file_name}
                      maxH="100%"
                      maxW="100%"
                      objectFit="cover"
                    />
                  ) : (
                    <Text fontSize="xs" textAlign="center" noOfLines={2}>
                      {att.file_name}
                    </Text>
                  )}
                </Box>
              ))}
            </HStack>
          )}
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};







