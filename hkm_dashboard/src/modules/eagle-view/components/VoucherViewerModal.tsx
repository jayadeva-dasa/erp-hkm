import React, { useState, useEffect } from 'react';
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
  Divider,
  Spinner,
  Center,
  Flex,
  Button,
} from '@chakra-ui/react';
import {
  DownloadIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ExternalLinkIcon,
} from '@chakra-ui/icons';

interface Attachment {
  file_name: string;
  file_url: string;
  file_size: number;
  is_private: number;
  file_type: 'pdf' | 'image' | 'other';
}

interface VoucherData {
  voucher_no: string;
  voucher_type: string;
  posting_date?: string;
  company?: string;
  attachments?: Attachment[];
}

interface VoucherViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  vouchers: VoucherData[];
  initialIndex: number;
}

export const VoucherViewerModal: React.FC<VoucherViewerModalProps> = ({
  isOpen,
  onClose,
  vouchers,
  initialIndex,
}) => {
  const [currentVoucherIndex, setCurrentVoucherIndex] = useState(initialIndex);
  const [currentAttachmentIndex, setCurrentAttachmentIndex] = useState(0);
  const [voucherLoading, setVoucherLoading] = useState(false);
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');
  const headerBg = useColorModeValue('gray.50', 'gray.700');

  // Reset attachment index when voucher changes
  useEffect(() => {
    setCurrentAttachmentIndex(0);
  }, [currentVoucherIndex]);

  // Reset to initial index when modal opens
  useEffect(() => {
    if (isOpen) {
      setCurrentVoucherIndex(initialIndex);
      setCurrentAttachmentIndex(0);
    }
  }, [isOpen, initialIndex]);

  if (!vouchers || vouchers.length === 0) {
    return null;
  }

  const currentVoucher = vouchers[currentVoucherIndex];
  const attachments = currentVoucher.attachments || [];
  const currentAttachment = attachments[currentAttachmentIndex];

  const handlePreviousVoucher = () => {
    setCurrentVoucherIndex((prev) => (prev > 0 ? prev - 1 : vouchers.length - 1));
  };

  const handleNextVoucher = () => {
    setCurrentVoucherIndex((prev) => (prev < vouchers.length - 1 ? prev + 1 : 0));
  };

  const handlePreviousAttachment = () => {
    setCurrentAttachmentIndex((prev) => (prev > 0 ? prev - 1 : attachments.length - 1));
  };

  const handleNextAttachment = () => {
    setCurrentAttachmentIndex((prev) => (prev < attachments.length - 1 ? prev + 1 : 0));
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i)) + ' ' + sizes[i];
  };

  const getFullUrl = (url: string) => {
    if (url.startsWith('http')) return url;
    return `${window.location.origin}${url}`;
  };

  const getVoucherUrl = () => {
    const baseUrl = window.location.origin;
    return `${baseUrl}/app/${currentVoucher.voucher_type.toLowerCase().replace(/ /g, '-')}/${currentVoucher.voucher_no}`;
  };

  const openVoucherInNewTab = () => {
    window.open(getVoucherUrl(), '_blank');
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="full">
      <ModalOverlay bg="blackAlpha.800" backdropFilter="blur(10px)" />
      <ModalContent maxW="98vw" maxH="98vh" m={4}>
        {/* Header */}
        <ModalHeader bg={headerBg} borderBottom="2px" borderColor={borderColor} pr={16}>
          <Flex justify="space-between" align="center">
            <VStack align="start" spacing={1} flex="1">
              <HStack spacing={3}>
                <Text fontSize="lg" fontWeight="bold">
                  {currentVoucher.voucher_type}: {currentVoucher.voucher_no}
                </Text>
                <Badge colorScheme="purple" fontSize="sm">
                  Voucher {currentVoucherIndex + 1} of {vouchers.length}
                </Badge>
                {attachments.length > 0 && (
                  <Badge colorScheme="blue" fontSize="sm">
                    {attachments.length} Attachment{attachments.length !== 1 ? 's' : ''}
                  </Badge>
                )}
              </HStack>
              {currentVoucher.posting_date && (
                <Text fontSize="sm" color="gray.600">
                  Date: {currentVoucher.posting_date}
                  {currentVoucher.company && ` • ${currentVoucher.company}`}
                </Text>
              )}
            </VStack>

            {/* Voucher Navigation */}
            <HStack spacing={2} flexShrink={0}>
              <Button
                size="sm"
                leftIcon={<ExternalLinkIcon />}
                onClick={openVoucherInNewTab}
                colorScheme="teal"
                variant="outline"
              >
                Open in New Tab
              </Button>
              <Divider orientation="vertical" h="30px" />
              <IconButton
                aria-label="Previous Voucher"
                icon={<ChevronLeftIcon boxSize={6} />}
                onClick={handlePreviousVoucher}
                size="md"
                colorScheme="blue"
                variant="outline"
              />
              <Text fontSize="sm" fontWeight="medium" minW="60px" textAlign="center">
                Voucher
              </Text>
              <IconButton
                aria-label="Next Voucher"
                icon={<ChevronRightIcon boxSize={6} />}
                onClick={handleNextVoucher}
                size="md"
                colorScheme="blue"
                variant="outline"
              />
            </HStack>
          </Flex>
        </ModalHeader>
        <ModalCloseButton top={4} right={4} />

        {/* Body - Split View */}
        <ModalBody p={0} overflow="hidden">
          <Flex h="calc(98vh - 120px)">
            {/* Left Side - Voucher Document */}
            <Box
              flex="1"
              borderRight="2px"
              borderColor={borderColor}
              position="relative"
              overflow="hidden"
            >
              <Box
                position="absolute"
                top={0}
                left={0}
                right={0}
                bottom={0}
                bg={bgColor}
              >
                {voucherLoading && (
                  <Center h="100%">
                    <Spinner size="xl" color="blue.500" />
                  </Center>
                )}
                <iframe
                  src={getVoucherUrl()}
                  width="100%"
                  height="100%"
                  title={`${currentVoucher.voucher_type} - ${currentVoucher.voucher_no}`}
                  style={{ border: 'none', display: voucherLoading ? 'none' : 'block' }}
                  onLoad={() => setVoucherLoading(false)}
                />
              </Box>
            </Box>

            {/* Right Side - Attachments */}
            <Box flex="1" display="flex" flexDirection="column" bg={bgColor}>
              {attachments.length === 0 ? (
                <Center h="100%" flexDirection="column" color="gray.500">
                  <Text fontSize="lg" mb={2}>
                    No Attachments
                  </Text>
                  <Text fontSize="sm">
                    This voucher has no attached files
                  </Text>
                </Center>
              ) : (
                <>
                  {/* Attachment Header */}
                  <Box
                    p={4}
                    borderBottom="1px"
                    borderColor={borderColor}
                    bg={headerBg}
                  >
                    <Flex justify="space-between" align="center">
                      <VStack align="start" spacing={1}>
                        <HStack>
                          <Text fontWeight="bold">Attachments</Text>
                          {attachments.length > 1 && (
                            <Badge colorScheme="blue">
                              {currentAttachmentIndex + 1} of {attachments.length}
                            </Badge>
                          )}
                        </HStack>
                        <HStack spacing={2} fontSize="sm" color="gray.600">
                          <Text>{currentAttachment.file_name}</Text>
                          <Badge>{formatFileSize(currentAttachment.file_size)}</Badge>
                        </HStack>
                      </VStack>

                      <HStack spacing={2}>
                        <Link
                          href={getFullUrl(currentAttachment.file_url)}
                          download
                          isExternal
                        >
                          <IconButton
                            aria-label="Download"
                            icon={<DownloadIcon />}
                            size="sm"
                            colorScheme="green"
                          />
                        </Link>
                        {attachments.length > 1 && (
                          <>
                            <Divider orientation="vertical" h="30px" />
                            <IconButton
                              aria-label="Previous Attachment"
                              icon={<ChevronLeftIcon />}
                              onClick={handlePreviousAttachment}
                              size="sm"
                              variant="outline"
                            />
                            <IconButton
                              aria-label="Next Attachment"
                              icon={<ChevronRightIcon />}
                              onClick={handleNextAttachment}
                              size="sm"
                              variant="outline"
                            />
                          </>
                        )}
                      </HStack>
                    </Flex>
                  </Box>

                  {/* Attachment Viewer */}
                  <Box flex="1" overflow="auto" p={4}>
                    <Box
                      h="100%"
                      bg={bgColor}
                      borderWidth="1px"
                      borderColor={borderColor}
                      borderRadius="md"
                      overflow="hidden"
                      display="flex"
                      alignItems="center"
                      justifyContent="center"
                    >
                      {currentAttachment.file_type === 'image' && (
                        <Image
                          src={getFullUrl(currentAttachment.file_url)}
                          alt={currentAttachment.file_name}
                          maxH="100%"
                          maxW="100%"
                          objectFit="contain"
                        />
                      )}

                      {currentAttachment.file_type === 'pdf' && (
                        <Box w="100%" h="100%">
                          <iframe
                            src={`${getFullUrl(currentAttachment.file_url)}#toolbar=1`}
                            width="100%"
                            height="100%"
                            title={currentAttachment.file_name}
                            style={{ border: 'none' }}
                          />
                        </Box>
                      )}

                      {currentAttachment.file_type === 'other' && (
                        <VStack spacing={4} p={8}>
                          <Text fontSize="lg" fontWeight="bold">
                            {currentAttachment.file_name}
                          </Text>
                          <Text color="gray.600">
                            Preview not available for this file type
                          </Text>
                          <Link
                            href={getFullUrl(currentAttachment.file_url)}
                            download
                          >
                            <Button
                              leftIcon={<DownloadIcon />}
                              colorScheme="green"
                              size="lg"
                            >
                              Download File
                            </Button>
                          </Link>
                        </VStack>
                      )}
                    </Box>
                  </Box>

                  {/* Thumbnail Strip for Multiple Attachments */}
                  {attachments.length > 1 && (
                    <Box
                      p={4}
                      borderTop="1px"
                      borderColor={borderColor}
                      bg={headerBg}
                    >
                      <HStack
                        spacing={2}
                        overflowX="auto"
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
                            borderColor={
                              index === currentAttachmentIndex ? 'blue.500' : borderColor
                            }
                            borderRadius="md"
                            cursor="pointer"
                            onClick={() => setCurrentAttachmentIndex(index)}
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
                    </Box>
                  )}
                </>
              )}
            </Box>
          </Flex>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

