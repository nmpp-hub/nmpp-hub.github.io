import ImageGallery from "react-image-gallery";
import "react-image-gallery/styles/image-gallery.css";

interface GalleryImage {
  src: string;
  title?: string;
}

interface Props {
  images: GalleryImage[];
}

export default function CodeGallery({ images }: Props) {
  const items = images.map((img) => ({
    original: img.src,
    thumbnail: img.src,
    originalTitle: img.title,
    description: img.title,
  }));

  return (
    <ImageGallery
      items={items}
      showPlayButton={false}
      lazyLoad={true}
    />
  );
}
