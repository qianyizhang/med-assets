import React from 'react';
import ReactMarkdown from 'react-markdown';
import rubric from './rubric.md?raw';

export function Rubric() {
  const table = rubric.match(/^\| Axis \|[^\n]+\n(?:\|[^\n]+\n)+/m);
  const chunks = table
    ? [rubric.slice(0, table.index), rubric.slice(table.index + table[0].length)]
    : [rubric];
  const rows = table?.[0]
    .trim()
    .split('\n')
    .filter((_, i) => i !== 1)
    .map((line) =>
      line
        .slice(1, -1)
        .split('|')
        .map((cell) => cell.trim()),
    );
  const ref = 'https://github.com/qianyizhang/med-assets/blob/main/docs/guides/asset-quality.md';
  const components = { a: ({ href, children }) => <a href={new URL(href, ref).href}>{children}</a> };
  return (
    <section className="ga-rubric">
      <ReactMarkdown components={components}>{chunks[0]}</ReactMarkdown>
      {rows && (
        <table>
          <thead>
            <tr>
              {rows[0].map((cell) => (
                <th key={cell}>{cell}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(1).map((row) => (
              <tr key={row[0]}>
                {row.map((cell, i) => (
                  <td key={i}>
                    <ReactMarkdown>{cell}</ReactMarkdown>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {chunks[1] && <ReactMarkdown components={components}>{chunks[1]}</ReactMarkdown>}
      <a href={ref}>Canonical rubric source ↗</a>
    </section>
  );
}
