// File Preview Modal Component

import React from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  Button,
  Image,
  Text,
  VStack,
  HStack,
  Badge,
  Icon,
} from '@chakra-ui/react';
import { FiDownload, FiFile } from 'react-icons/fi';
import type { S3File } from '../types';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: S3File | null;
  onDownload: (file: S3File) => void;
}

export const FilePreviewModal: React.FC<FilePreviewModalProps> = ({
  isOpen,
  onClose,
  file,
  onDownload,
}) => {
  if (!file) return null;

  const isImage = file.file_type.startsWith('image/');
  const isPDF = file.file_type === 'application/pdf';

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="4xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          <VStack align="start" spacing={2}>
            <HStack>
              <Icon as={FiFile} />
              <Text>{file.file_name}</Text>
            </HStack>
            <HStack spacing={2}>
              <Badge colorScheme="blue">{file.size_formatted}</Badge>
              <Badge colorScheme="green">{file.last_modified_formatted}</Badge>
            </HStack>
          </VStack>
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          {isImage ? (
            <Image
              src={file.url}
              alt={file.file_name}
              maxH="600px"
              objectFit="contain"
              mx="auto"
            />
          ) : isPDF ? (
            <iframe
              src={file.url}
              width="100%"
              height="600px"
              title={file.file_name}
              style={{ border: 'none' }}
            />
          ) : (
            <VStack spacing={4} py={8}>
              <Icon as={FiFile} boxSize={16} color="gray.400" />
              <Text color="gray.600">Preview not available for this file type</Text>
              <Text fontSize="sm" color="gray.500">{file.file_type}</Text>
            </VStack>
          )}
        </ModalBody>

        <ModalFooter>
          <Button
            leftIcon={<FiDownload />}
            colorScheme="blue"
            onClick={() => onDownload(file)}
            mr={3}
          >
            Download
          </Button>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

