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
  HStack,
  IconButton,
  Text,
  useColorModeValue,
} from '@chakra-ui/react';
import { ChevronLeftIcon, ChevronRightIcon } from '@chakra-ui/icons';

interface ImageModalProps {
  isOpen: boolean;
  onClose: () => void;
  images: string[];
  initialIndex?: number;
  assetName?: string;
}

export const ImageModal: React.FC<ImageModalProps> = ({
  isOpen,
  onClose,
  images,
  initialIndex = 0,
  assetName,
}) => {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  // Filter out invalid images and ensure we have valid images
  const validImages = images.filter((img) => img && typeof img === 'string' && img.trim() !== '');

  const handlePrevious = () => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : validImages.length - 1));
  };

  const handleNext = () => {
    setCurrentIndex((prev) => (prev < validImages.length - 1 ? prev + 1 : 0));
  };

  const getFullUrl = (url: string | undefined | null) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    return `${window.location.origin}${url}`;
  };
  
  // Reset index if current index is out of bounds
  useEffect(() => {
    if (isOpen && validImages.length > 0) {
      const safeIndex = Math.min(initialIndex, validImages.length - 1);
      setCurrentIndex(Math.max(0, safeIndex));
    }
  }, [isOpen, initialIndex, validImages.length]);

  if (!isOpen || validImages.length === 0) {
    return null;
  }

  const currentImage = validImages[currentIndex];

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="6xl" isCentered>
      <ModalOverlay bg="blackAlpha.800" />
      <ModalContent bg={bgColor} maxH="90vh">
        <ModalHeader>
          <HStack justify="space-between">
            <Text>
              {assetName ? `${assetName} - ` : ''}Image {currentIndex + 1} of {validImages.length}
            </Text>
          </HStack>
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <HStack spacing={2} align="stretch" h="70vh">
            {validImages.length > 1 && (
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
              p={4}
            >
              <Image
                src={getFullUrl(currentImage)}
                alt={`Image ${currentIndex + 1}`}
                maxH="100%"
                maxW="100%"
                objectFit="contain"
                cursor="pointer"
                onClick={handleNext}
              />
            </Box>

            {validImages.length > 1 && (
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
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};

