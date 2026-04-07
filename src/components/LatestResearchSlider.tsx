import ImageGallery from "react-image-gallery";
import "react-image-gallery/styles/image-gallery.css";

interface PublicationItem {
  type: "publication";
  title: string;
  year?: number;
  authors?: string;
  abstract?: string;
  url: string;
}

interface DissertationItem {
  type: "dissertation";
  title: string;
  year?: number;
  author: string;
  degree: string;
  abstract?: string;
  link: string;
}

type ResearchItem = PublicationItem | DissertationItem;

interface Props {
  items: ResearchItem[];
}

// 1×1 transparent GIF — required by react-image-gallery but not rendered
const BLANK = "data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==";

export default function LatestResearchSlider({ items }: Props) {
  const galleryItems = items.map(item => ({ original: BLANK, item }));

  const renderItem = (galleryItem: any) => {
    const item: ResearchItem = galleryItem.item;
    const href = item.type === "publication" ? item.url : item.link;
    const linkLabel = item.type === "publication" ? "Read Publication →" : "Read Dissertation →";
    const metaRight =
      item.type === "publication"
        ? item.authors
        : `${item.degree} by ${item.author}`;

    return (
      <div className="rsg-slide">
        <div className="rsg-type">
          {item.type === "publication" ? "Publication" : "Dissertation"}
        </div>
        <h3 className="rsg-title">{item.title}</h3>
        <p className="rsg-meta">
          {item.year && <span className="rsg-year">{item.year}</span>}
          {metaRight && <span className="rsg-authors">{metaRight}</span>}
        </p>
        {item.abstract && (
          <p className="rsg-abstract">{item.abstract.substring(0, 180)}…</p>
        )}
        <a href={href} className="rsg-link">{linkLabel}</a>
      </div>
    );
  };

  return (
    <ImageGallery
      items={galleryItems}
      renderItem={renderItem}
      showThumbnails={false}
      showPlayButton={false}
      showFullscreenButton={false}
      showBullets={true}
      showNav={true}
      autoPlay={true}
      slideInterval={6000}
    />
  );
}
