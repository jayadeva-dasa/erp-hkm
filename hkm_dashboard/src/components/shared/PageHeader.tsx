import { ArrowBackIcon } from '@chakra-ui/icons';
import { Badge, Flex, Heading, IconButton, Stack, Text } from '@chakra-ui/react';
import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

interface StatusProps {
  label: string;
  colorScheme?: string;
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  status?: StatusProps | null;
  backTo?: string;
  children?: ReactNode;
}

const PageHeader = ({ title, subtitle, status, backTo = '/', children }: PageHeaderProps) => {
  const navigate = useNavigate();

  const handleBack = () => {
    if (backTo) {
      navigate(backTo);
      return;
    }
    navigate(-1);
  };

  return (
    <Flex
      direction={{ base: 'column', md: 'row' }}
      align={{ base: 'flex-start', md: 'center' }}
      justify="space-between"
      gap={4}
      mb={6}
    >
      <Flex align="center" gap={4} flexWrap="wrap">
        <IconButton
          aria-label="Back to Dashboard"
          variant="ghost"
          colorScheme="orange"
          icon={<ArrowBackIcon />}
          onClick={handleBack}
        />
        <Stack spacing={1} minW={{ base: '100%', md: 'auto' }}>
          <Flex align="center" gap={2} flexWrap="wrap">
            <Heading size="lg">{title}</Heading>
            {status?.label && (
              <Badge colorScheme={status.colorScheme || 'green'}>{status.label}</Badge>
            )}
          </Flex>
          {subtitle ? (
            <Text color="gray.600" fontSize="sm">
              {subtitle}
            </Text>
          ) : null}
        </Stack>
      </Flex>
      {children}
    </Flex>
  );
};

export default PageHeader;




