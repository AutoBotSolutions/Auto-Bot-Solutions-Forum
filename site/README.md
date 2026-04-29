# AutoBot Solutions Forum - GitHub Pages Site

This directory contains the GitHub Pages website for the AutoBot Solutions Forum project.

## Features

- **Futuristic Sci-Fi Theme**: Neon colors, glowing effects, and animated backgrounds
- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean interface with smooth animations and transitions
- **Feature Showcase**: Displays all forum capabilities and technology stack
- **Quick Start Guide**: Includes installation instructions for developers

## Files

- `index.html` - Main HTML file with project information
- `style.css` - Futuristic sci-fi themed stylesheet
- `README.md` - This file

## Deployment

### GitHub Pages Setup

1. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Under "Source", select "Deploy from a branch"
   - Choose the branch (usually `main` or `gh-pages`)
   - Set the folder to `/site` (or move these files to the root if preferred)
   - Click Save

2. **Alternative: Using gh-pages branch**:
   ```bash
   git checkout -b gh-pages
   git checkout main -- site
   mv site/* .
   rm -rf site
   git add .
   git commit -m "Add GitHub Pages site"
   git push origin gh-pages
   ```

3. **Custom Domain** (optional):
   - Add a CNAME file with your custom domain
   - Configure DNS settings with your domain provider

## Customization

### Colors
Edit the CSS variables in `style.css`:
```css
:root {
    --neon-cyan: #00f5ff;
    --neon-magenta: #ff00ff;
    --neon-purple: #9d00ff;
    --neon-green: #00ff88;
    --neon-orange: #ffaa00;
    /* ... */
}
```

### Content
Edit `index.html` to update:
- Project title and description
- Feature list
- Technology stack
- Installation instructions
- Links and URLs

### Fonts
The site uses Google Fonts:
- Orbitron (headings)
- Rajdhani (body text)

You can change these in the HTML `<head>` section.

## Performance

- Optimized CSS with minimal animations
- Font preconnect for faster loading
- Responsive images (if added)
- Minimal JavaScript (no external dependencies)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Same as the main project. See LICENSE file in the root directory.

## Support

For issues or questions:
- GitHub Issues: [your-repo-url]/issues
- Documentation: See the main project README

## Credits

- Owner: Robert Trenaman
- Company: Auto Bot Solution (Software Customs)
- Email: autobotsolution@gmail.com
- Location: Flushing MI
