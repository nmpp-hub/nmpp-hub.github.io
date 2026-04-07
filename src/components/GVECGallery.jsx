import React from 'react';
import ImageGallery from 'react-image-gallery';
import 'react-image-gallery/styles/css/image-gallery.css';

// Example images, replace with your actual images
const images = [
  {
    original: 'https://raw.githubusercontent.com/struphy-hub/struphy/devel/README_files/figure-commonmark/cell-2-output-1.png',
    thumbnail: 'https://raw.githubusercontent.com/struphy-hub/struphy/devel/README_files/figure-commonmark/cell-2-output-1.png',
    description: 'GVEC simulation result 1',
  },
  {
    original: 'https://raw.githubusercontent.com/struphy-hub/struphy/devel/README_files/figure-commonmark/cell-2-output-2.png',
    thumbnail: 'https://raw.githubusercontent.com/struphy-hub/struphy/devel/README_files/figure-commonmark/cell-2-output-2.png',
    description: 'GVEC simulation result 2',
  },
  // Add more images as needed
];

const GVECGallery = () => (
  <div style={{ maxWidth: '700px', margin: '2rem auto' }}>
    <h2>Gallery</h2>
    <ImageGallery items={images} showPlayButton={false} />
  </div>
);

export default GVECGallery;
