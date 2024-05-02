import * as React from 'react';
import PropTypes from 'prop-types';

import Box from '@mui/material/Box';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Container from '@mui/material/Container';
import Divider from '@mui/material/Divider';
import MenuItem from '@mui/material/MenuItem';
import Drawer from '@mui/material/Drawer';
import MenuIcon from '@mui/icons-material/Menu';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';

import SitemarkIcon from './SitemarkIcon';

function AppAppBar() {
  const [open, setOpen] = React.useState(false);

  const toggleDrawer = (newOpen) => () => {
    setOpen(newOpen);
  };

  const scrollToSection = (sectionId) => {
    const sectionElement = document.getElementById(sectionId);
    const offset = 128;
    if (sectionElement) {
      const targetScroll = sectionElement.offsetTop - offset;
      sectionElement.scrollIntoView({ behavior: 'smooth' });
      window.scrollTo({
        top: targetScroll,
        behavior: 'smooth',
      });
      setOpen(false);
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        boxShadow: 0,
        bgcolor: 'transparent',
        backgroundImage: 'none',
        mt: 2,
      }}
    >
      <Container maxWidth="lg">
        <Toolbar
          variant="regular"
          sx={(theme) => ({
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0,
            borderRadius: '999px',
            bgcolor:
              theme.palette.mode === 'light'
                ? 'hsla(10, 60%, 99%, 0.6)'
                : 'hsla(10, 0%, 0%, 0.7)',
            backdropFilter: 'blur(24px)',
            maxHeight: 40,
            border: '1px solid',
            borderColor: 'divider',
            boxShadow:
              theme.palette.mode === 'light'
                ? '0 1px 2px hsla(10, 0%, 0%, 0.05), 0 2px 12px hsla(10, 100%, 80%, 0.5)'
                : '0 1px 2px hsla(10, 0%, 0%, 0.5), 0 2px 12px hsla(10, 100%, 25%, 0.3)',
          })}
        >
          <Box
            sx={{
              flexGrow: 1,
              display: 'flex',
              alignItems: 'center',
              px: 0,
            }}
          >
            <SitemarkIcon />
            <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
              <Button
                variant="text"
                color="primary"
                size="medium"
                onClick={() => scrollToSection('features')}
              >
                Features
              </Button>
             {/* <Button
                variant="text"
                color="primary"
                size="medium"
                onClick={() => scrollToSection('testimonials')}
              >
                Testimonials
          </Button> */}
              <Button
                variant="text"
                color="primary"
                size="medium"
                onClick={() => scrollToSection('highlights')}
              >
                Highlights
              </Button>
              <Button
                variant="text"
                color="primary"
                size="medium"
                onClick={() => scrollToSection('pricing')}
              >
                Pricing
              </Button>
              <Button
                variant="text"
                color="primary"
                size="medium"
                onClick={() => scrollToSection('faq')}
                sx={{ minWidth: 0 }}
              >
                FAQ
              </Button>
            </Box>
          </Box>
          <Box
            sx={{
              display: { xs: 'none', md: 'flex' },
              gap: 0.5,
              alignItems: 'center',
            }}
          >
            <Button color="primary" variant="text" size="small" href="https://multivac.sunholo.com">
              Sign in
            </Button>
            <Button color="primary" variant="contained" size="small" href="https://multivac.sunholo.com">
              Sign up
            </Button>
          </Box>
          <Box sx={{ display: { sm: 'flex', md: 'none' } }}>
            <IconButton aria-label="Menu button" onClick={toggleDrawer(true)}>
              <MenuIcon />
            </IconButton>
            <Drawer anchor="top" open={open} onClose={toggleDrawer(false)}>
              <Box
                sx={{
                  p: 2,
                  backgroundColor: 'background.default',
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <IconButton onClick={toggleDrawer(false)}>
                    <CloseRoundedIcon />
                  </IconButton>
                </Box>
                <Divider sx={{ my: 3 }} />
                <MenuItem onClick={() => scrollToSection('features')}>
                  Features
                </MenuItem>
                <MenuItem onClick={() => scrollToSection('highlights')}>
                  Highlights
                </MenuItem>
                <MenuItem onClick={() => scrollToSection('pricing')}>
                  Pricing
                </MenuItem>
                <MenuItem onClick={() => scrollToSection('faq')}>FAQ</MenuItem>
                <MenuItem>
                  <Button color="primary" variant="contained" fullWidth href="https://multivac.sunholo.com">
                    Sign up
                  </Button>
                </MenuItem>
                <MenuItem>
                  <Button color="primary" variant="outlined" fullWidth href="https://multivac.sunholo.com">
                    Sign in
                  </Button>
                </MenuItem>
              </Box>
            </Drawer>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
}


export default AppAppBar;
