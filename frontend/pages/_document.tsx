import { Html, Head, Main, NextScript } from "next/document";

/** Compatibility document for Next's legacy page collector during production builds. */
export default function Document() {
  return (
    <Html lang="en">
      <Head />
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
