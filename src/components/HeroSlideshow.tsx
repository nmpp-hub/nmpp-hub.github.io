import ImageGallery from "react-image-gallery";
import "react-image-gallery/styles/image-gallery.css";

interface HeroImage {
  src: string;
  alt?: string;
  title: string;
  caption: string;
}

interface Props {
  images: HeroImage[];
}

export default function HeroSlideshow({ images }: Props) {
  const items = images.map(img => ({
    original: img.src,
    originalAlt: img.alt ?? img.title,
    slideTitle: img.title,
    slideCaption: img.caption,
  }));

  const renderItem = (item: any) => (
    <div className="hero-gallery-slide">
      <img
        src={item.original}
        alt={item.originalAlt}
        className="hero-gallery-img"
      />
      <div className="hero-gallery-caption">
        <strong>{item.slideTitle}</strong>
        {item.slideCaption}
      </div>
    </div>
  );

  return (
    <ImageGallery
      items={items}
      renderItem={renderItem}
      showThumbnails={false}
      showPlayButton={false}
      showFullscreenButton={false}
      showBullets={true}
      autoPlay={true}
      slideInterval={4800}
    />
  );
}
