#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BootProgress { Starting(u8), CheckingFilesystem, Finalizing, Completed }

#[derive(Debug)]
pub struct PlymouthSplash {
    pub progress: BootProgress,
    pub prompt_active: bool,
}

impl PlymouthSplash {
    pub fn new() -> Self { Self { progress: BootProgress::Starting(0), prompt_active: false } }
    pub fn update_percent(&mut self, p: u8) {
        self.progress = if p >= 100 { BootProgress::Completed } else { BootProgress::Starting(p) };
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_plymouth_splash_progress_aaa() {
        // Arrange
        let mut splash = PlymouthSplash::new();
        // Act
        splash.update_percent(50);
        // Assert
        assert_eq!(splash.progress, BootProgress::Starting(50));
        splash.update_percent(100);
        assert_eq!(splash.progress, BootProgress::Completed);
    }
}
