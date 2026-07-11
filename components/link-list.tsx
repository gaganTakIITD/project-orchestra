import Link from "next/link";
import { memo } from "react";

interface LinkItem {
  label: string;
  href: string;
}

interface LinkListProps {
  items: LinkItem[];
  className?: string;
  itemClassName?: string;
  external?: boolean;
}

/**
 * Reusable link list component - memoized to prevent unnecessary re-renders
 * Used in navigation, footers, and sidebar components
 */
export const LinkList = memo(function LinkList({
  items,
  className = "flex flex-col gap-3",
  itemClassName = "text-sm hover:opacity-75 transition-opacity",
  external = false,
}: LinkListProps) {
  return (
    <ul className={className}>
      {items.map((item) => (
        <li key={item.href}>
          {external ? (
            <a 
              href={item.href} 
              target="_blank" 
              rel="noopener noreferrer"
              className={itemClassName}
            >
              {item.label}
            </a>
          ) : (
            <Link href={item.href} className={itemClassName}>
              {item.label}
            </Link>
          )}
        </li>
      ))}
    </ul>
  );
});

export default LinkList;
